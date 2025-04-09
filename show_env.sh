#!/bin/bash

#####################################################################
# 脚本名称: show_env.sh
# 描述: 此脚本用于显示系统环境信息，包括:
#      - Git仓库信息
#      - 操作系统信息
#      - CPU和内存信息
#      - Docker和Python版本信息
#####################################################################

# 函数: get_distro_info
# 描述: 获取Linux发行版信息和内核版本
# 返回: 发行版ID、版本号和内核版本的字符串
get_distro_info() {
    # 尝试使用lsb_release命令获取发行版信息
    local distro_id=$(lsb_release -i -s 2>/dev/null)
    local distro_version=$(lsb_release -r -s 2>/dev/null)
    local kernel_version=$(uname -r)

    # 如果lsb_release命令不可用，则从/etc/*-release文件中解析信息
    if [ -z "$distro_id" ] || [ -z "$distro_version" ]; then
        distro_id=$(grep '^ID=' /etc/*-release | cut -d= -f2 | tr -d '"')
        distro_version=$(grep '^VERSION_ID=' /etc/*-release | cut -d= -f2 | tr -d '"')
    fi

    echo "$distro_id $distro_version (Kernel version: $kernel_version)"
}

# 获取Git仓库名称
# 如果当前目录是Git仓库，则获取仓库名称；否则返回提示信息
git_repo_name=''
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    git_repo_name=$(basename "$(git rev-parse --show-toplevel)")
    if [ $? -ne 0 ]; then
        git_repo_name="(Can't get repo name)"
    fi
else
    git_repo_name="It NOT a Git repo"
fi

# 获取CPU架构信息
cpu_model=$(uname -m)

# 获取系统总内存大小（以人类可读格式显示）
memory_size=$(free -h | grep Mem | awk '{print $2}')

# 获取Docker版本信息
# 如果Docker未安装，则返回相应提示
docker_version=''
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | cut -d ' ' -f3)
else
    docker_version="Docker not installed"
fi

# 获取Python版本信息
# 如果Python未安装，则返回相应提示
python_version=''
if command -v python &> /dev/null; then
    python_version=$(python --version | cut -d ' ' -f2)
else
    python_version="Python not installed"
fi

# 输出所有收集到的系统信息
echo "Current Repository: $git_repo_name"

# 获取并显示最新的Git提交ID
# 如果不是Git仓库或Git未安装，则显示错误信息
git_version=$(git log -1 --pretty=format:'%h')

if [ -z "$git_version" ]; then
    echo "Commit Id: The current directory is not a Git repository, or the Git command is not installed."
else
    echo "Commit Id: $git_version"
fi

# 显示系统环境信息
echo "Operating system: $(get_distro_info)"
echo "CPU Type: $cpu_model"
echo "Memory: $memory_size"
echo "Docker Version: $docker_version"
echo "Python Version: $python_version"
