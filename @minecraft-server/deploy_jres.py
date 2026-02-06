import os
import urllib.request
import tarfile
import sys
import shutil
import hashlib
import tomllib
import urllib.parse

CACHE_DIR = "/tmp/jre-pkg"
BASE_TARGET_DIR = "/data/runtime"
CONFIG_FILE = "./jre-pkgs.toml"
ARCH = os.environ.get("TARGETARCH", "amd64")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] Config file {CONFIG_FILE} not found.")
        sys.exit(1)
    with open(CONFIG_FILE, mode="rb") as fp:
        return tomllib.load(fp)


def generate_temurin_url(full_version, docker_arch):
    """根据版本号自动构建 Adoptium 下载链接"""
    arch_map = {"amd64": "x64", "arm64": "aarch64"}
    if docker_arch not in arch_map:
        print(f"[ERROR] Unsupported architecture: {docker_arch}")
        sys.exit(1)

    repo_arch = arch_map[docker_arch]
    ver_major = full_version.split('.')[0]
    tag_version = urllib.parse.quote(f"jdk-{full_version}")
    filename_version = full_version.replace('+', '_')

    url = (
        f"https://github.com/adoptium/temurin{ver_major}-binaries/releases/download/"
        f"{tag_version}/"
        f"OpenJDK{ver_major}U-jre_{repo_arch}_linux_hotspot_{filename_version}.tar.gz"
    )
    return url


def calculate_sha256(filepath):
    """计算文件 Hash"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"[WARN] Error calculating hash for {filepath}: {e}")
        return None


def download_file(url, filepath):
    """单纯的下载函数"""
    print(f"Downloading {url} ...")
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        urllib.request.urlretrieve(url, filepath)
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        raise


def phase_1_prepare_cache(config):
    """
    第一阶段：准备所有文件。
    遍历配置，检查缓存。如果缺文件或 Hash 不对，则下载。
    返回一个列表，包含所有【准备好等待解压】的任务信息。
    """
    print(f"\n>>> [Phase 1] Checking Cache & Downloading for {ARCH}...")
    extraction_tasks = []

    for key, info in config.items():
        # 1. 解析配置
        arch_data = info.get(ARCH)
        if not arch_data:
            print(f"[SKIP] No config for {key} on {ARCH}")
            continue

        # 优先用显式 URL，没有则自动生成
        url = arch_data.get('url')
        if not url:
            version = info.get('version')
            if version:
                url = generate_temurin_url(version, ARCH)
            else:
                print(f"[WARN] Incomplete config for {key}, skipping.")
                continue

        expected_hash = arch_data.get('sha256')
        if not expected_hash:
            print(f"[WARN] Missing sha256 for {key}, skipping.")
            continue

        # 2. 准备路径
        try:
            ver_short = key.split('_')[1]  # JRE_25 -> 25
            dest_dir = os.path.join(BASE_TARGET_DIR, f"jre-{ver_short}")
        except IndexError:
            continue

        cache_filename = os.path.basename(url)
        cache_file = os.path.join(CACHE_DIR, cache_filename)

        # 3. 检查缓存状态
        file_ready = False
        if os.path.exists(cache_file):
            print(f"Checking existing file: {cache_filename}")
            if calculate_sha256(cache_file) == expected_hash:
                print(f"[OK] Cache Hit & Verified: {cache_filename}")
                file_ready = True
            else:
                print(f"[BAD] Hash mismatch, deleting: {cache_filename}")
                os.remove(cache_file)

        # 4. 如果没准备好，开始下载
        if not file_ready:
            try:
                download_file(url, cache_file)
                # 下载完立即校验
                if calculate_sha256(cache_file) == expected_hash:
                    print(f"[OK] Downloaded & Verified: {cache_filename}")
                else:
                    print(f"[FATAL] Hash mismatch after download: {cache_filename}")
                    sys.exit(1)
            except Exception:
                sys.exit(1)  # 下载失败直接终止构建

        # 5. 加入任务列表
        extraction_tasks.append({
            "name": key,
            "tar_path": cache_file,
            "dest_dir": dest_dir
        })

    return extraction_tasks


def phase_2_extract(tasks):
    """
    第二阶段：批量解压。
    """
    print(f"\n>>> [Phase 2] Extracting {len(tasks)} packages...")

    if not tasks:
        print("Nothing to extract.")
        return

    for task in tasks:
        tar_path = task['tar_path']
        dest_dir = task['dest_dir']
        name = task['name']

        print(f"Extracting [{name}] to {dest_dir} ...")

        # 清理旧目录
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.makedirs(dest_dir, exist_ok=True)

        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                def members(tf):
                    for member in tf.getmembers():
                        # 去除第一层目录 (strip-components=1)
                        if '/' in member.name:
                            member.name = member.name.split('/', 1)[1]
                            yield member

                tar.extractall(path=dest_dir, members=members(tar), numeric_owner=True, filter='data')

        except Exception as e:
            print(f"[ERROR] Failed to extract {tar_path}: {e}")
            # 解压失败通常意味着文件损坏或磁盘满了，清理现场并报错
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            sys.exit(1)


def main():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)

    config = load_config()

    # 1. 先把所有文件搞定 (下载或确认缓存)
    tasks = phase_1_prepare_cache(config)

    # 2. 如果第一步都成功了，再一次性解压
    phase_2_extract(tasks)

    print("\n>>> All JREs deployed successfully.")


if __name__ == "__main__":
    main()
