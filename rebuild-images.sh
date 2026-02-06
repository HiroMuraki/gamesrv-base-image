#!/bin/bash
set -e

# 遍历当前目录下所有以 @ 开头的目录
for category_path in ./@*/; do
    # 检查是否存在匹配的目录，如果没有则跳过（防止没有匹配时报错）
    [ -d "$category_path" ] || continue

    # ==============================
    # 1. 路径与名称处理
    # ==============================
    
    # 去掉末尾的斜杠 (例如: ./@minecraft/ -> ./@minecraft)
    category_dir=${category_path%/}
    
    # 去掉开头的 ./ (例如: ./@minecraft -> @minecraft)
    clean_dir_name=${category_dir#./}
    
    # 去掉开头的 @ 作为镜像名 (例如: @minecraft -> minecraft)
    image_name=${clean_dir_name#@}

    # 构造完整镜像 Tag (例如: minecraft:latest)
    # 如果你需要推送到 ghcr，可以在这里加上前缀，例如: ghcr.io/用户名/$image_name:latest
    full_image_tag="${image_name}:latest"

    echo "=========================================="
    echo "发现项目目录: $category_dir"
    echo "目标镜像名称: $full_image_tag"

    # ==============================
    # 2. 检查 Dockerfile
    # ==============================
    
    # 直接在目录下找 Dockerfile
    if [ ! -f "${category_path}Dockerfile" ]; then
        echo "⚠️  [跳过] 目录 ${category_dir} 中未找到 Dockerfile"
        echo "=========================================="
        continue
    fi

    # ==============================
    # 3. 执行构建
    # ==============================
    
    echo "🔨 正在构建镜像..."
    echo "   构建上下文: $category_path"

    if docker build -t "$full_image_tag" "$category_path"; then
        echo "✅ 构建成功: $full_image_tag"
    else
        echo "❌ 构建失败: $full_image_tag"
        exit 1 # 如果你是放在 CI 里跑，建议失败时直接退出，让 CI 报错
    fi
    
    echo "=========================================="
done

echo "🎉 所有构建任务完成。"