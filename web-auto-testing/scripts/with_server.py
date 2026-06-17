#!/usr/bin/env python3
"""
启动一个或多个服务器，等待它们就绪后运行命令，最后自动清理。

使用场景：
- 需要在测试前自动启动开发服务器（如 Vite、Webpack）
- 需要后端服务运行
- CI/CD 环境中需要临时启动服务

用法:
    # 单个服务器
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # 多个服务器（例如前端 + 后端）
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py

    # 运行 Playwright 测试
    python scripts/with_server.py \
      --server "npm run dev" --port 5173 \
      -- npx playwright test
"""

import subprocess
import socket
import time
import sys
import argparse

def is_server_ready(port, timeout=30):
    """通过轮询端口等待服务器就绪"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(
        description='运行命令前自动启动一个或多个服务器',
        epilog="""
示例:
  %(prog)s --server "npm run dev" --port 5173 -- python test.py
  %(prog)s --server "npm start" --port 3000 -- npx playwright test
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--server',
        action='append',
        dest='servers',
        required=True,
        help='服务器启动命令（可重复使用）'
    )
    parser.add_argument(
        '--port',
        action='append',
        dest='ports',
        type=int,
        required=True,
        help='每个服务器对应的端口（必须与 --server 数量匹配）'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='每个服务器的超时时间（秒），默认 30'
    )
    parser.add_argument(
        'command',
        nargs=argparse.REMAINDER,
        help='服务器就绪后要运行的命令'
    )

    args = parser.parse_args()

    # 移除 '--' 分隔符（如果存在）
    if args.command and args.command[0] == '--':
        args.command = args.command[1:]

    if not args.command:
        print("错误：未指定要运行的命令")
        sys.exit(1)

    # 解析服务器配置
    if len(args.servers) != len(args.ports):
        print("错误：--server 和 --port 的数量必须匹配")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({'cmd': cmd, 'port': port})

    server_processes = []

    try:
        # 启动所有服务器
        for i, server in enumerate(servers):
            print(f"正在启动服务器 {i+1}/{len(servers)}: {server['cmd']}")

            # 使用 shell=True 以支持 cd 和 && 等命令
            process = subprocess.Popen(
                server['cmd'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            server_processes.append(process)

            # 等待此服务器就绪
            print(f"等待端口 {server['port']} 上的服务器就绪...")
            if not is_server_ready(server['port'], timeout=args.timeout):
                raise RuntimeError(
                    f"服务器在 {args.timeout} 秒内未能在端口 {server['port']} 上启动"
                )

            print(f"✓ 服务器已在端口 {server['port']} 上就绪")

        print(f"\n所有 {len(servers)} 个服务器已就绪\n")

        # 运行命令
        print(f"运行命令: {' '.join(args.command)}\n")
        result = subprocess.run(args.command)
        sys.exit(result.returncode)

    finally:
        # 清理所有服务器
        print(f"\n正在停止 {len(server_processes)} 个服务器...")
        for i, process in enumerate(server_processes):
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print(f"✓ 服务器 {i+1} 已停止")
        print("所有服务器已停止")


if __name__ == '__main__':
    main()
