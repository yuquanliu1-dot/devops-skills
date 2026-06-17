#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版测试生成脚本 - 自动处理认证

特点:
1. 自动检测登录页面
2. 自动保存认证状态
3. 生成包含认证处理的测试代码
4. 验证选择器稳定性

Usage:
    python scripts/generate_test_with_auth.py --url https://chat.deepseek.com/ --output tests/chat.spec.js
    python scripts/generate_test_with_auth.py --interactive
"""

import argparse
import sys
import os
import json
import time
import io

# 设置标准输出编码为 UTF-8（兼容 Windows）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("错误: 未安装 playwright")
    print("请运行: pip install playwright")
    print("然后运行: playwright install")
    sys.exit(1)


class AuthDetector:
    """认证状态检测器"""

    # 登录页面特征
    LOGIN_INDICATORS = [
        '请输入手机号',
        '请输入验证码',
        '发送验证码',
        '注册登录',
        '微信扫码登录',
        '登录账号',
        '密码登录',
        '手机号登录',
        'Log in',
        'Sign in',
        'email'
    ]

    # 登录成功后的特征
    LOGGED_IN_INDICATORS = [
        '给 DeepSeek 发送消息',
        '发送消息',
        'message',
        'textarea',
        'input'
    ]

    @staticmethod
    def is_login_page(page):
        """检测是否在登录页面"""
        try:
            # 方法1: 检查页面文本特征
            page_content = page.content()
            for indicator in AuthDetector.LOGIN_INDICATORS:
                if indicator in page_content:
                    print(f"  [检测] 发现登录页面特征: '{indicator}'")
                    return True

            # 方法2: 检查URL
            current_url = page.url
            login_keywords = ['/login', '/signin', '/auth', '/sign_in']
            for keyword in login_keywords:
                if keyword in current_url.lower():
                    print(f"  [检测] URL包含登录关键词: {keyword}")
                    return True

            return False
        except Exception as e:
            print(f"  [警告] 检测登录页面时出错: {e}")
            return False

    @staticmethod
    def is_logged_in(page):
        """检测是否已登录"""
        try:
            page_content = page.content()

            # 如果检测到登录页面特征，则未登录
            if AuthDetector.is_login_page(page):
                return False

            # 检查是否有登录后的特征
            for indicator in AuthDetector.LOGGED_IN_INDICATORS:
                if indicator in page_content:
                    print(f"  [检测] 发现登录后特征: '{indicator}'")
                    return True

            return False
        except Exception as e:
            print(f"  [警告] 检测登录状态时出错: {e}")
            return False


def generate_test_code(url, auth_file='auth.json', test_name='测试'):
    """生成包含认证处理的测试代码"""

    code = f"""const {{ test, expect }} = require('@playwright/test');
const AuthHelper = require('../utils/auth-helper');

/**
 * {test_name}
 *
 * 自动生成的测试脚本 - 包含认证处理
 *
 * 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
 * 目标URL: {url}
 * 认证文件: {auth_file}
 *
 * 使用说明:
 * 1. 首次运行时，脚本会自动打开浏览器让您登录
 * 2. 登录成功后，认证状态会自动保存到 {auth_file}
 * 3. 后续运行时会自动使用保存的认证状态
 *
 * 运行测试:
 *   npx playwright test {os.path.basename(test_file) if 'test_file' in locals() else 'test.spec.js'} --reporter=html
 */

test.describe('{test_name}', () => {{
  let authHelper;

  test.beforeEach(async ({{ page }}) => {{
    authHelper = new AuthHelper(page);
  }});

  test('应该能够访问页面并完成基本操作', async ({{ page }}) => {{
    // 步骤1: 尝试使用保存的认证状态
    const loginSuccess = await authHelper.loginWithSavedState('{auth_file}');

    if (!loginSuccess) {{
      console.log('[WARNING]  认证文件不存在或已过期');
      console.log('[TIP] 请运行以下命令生成认证文件:');
      console.log('   node scripts/setup-auth.js {url}');
      test.skip(true, '需要认证文件');
      return;
    }}

    // 步骤2: 导航到目标页面
    console.log('[INFO] 正在导航到目标页面...');
    await page.goto('{url}');
    await page.waitForLoadState('networkidle');

    // 步骤3: 验证是否成功登录
    const isLoggedIn = await authHelper.isLoggedIn();
    if (!isLoggedIn) {{
      console.log('[ERROR] 认证文件已过期');
      test.skip(true, '认证文件已过期,请重新生成');
      return;
    }}

    console.log('[OK] 已成功登录');

    // 步骤4: 在这里添加您的测试逻辑
    // 示例: 查找输入框
    // const input = page.getByRole('textbox', {{ name: '搜索' }});
    // await expect(input).toBeVisible();

    // TODO: 根据实际需求添加测试步骤

    console.log('[OK] 测试完成');
  }});
}}
"""

    return code


def scan_and_save_auth(url, auth_file='auth.json', timeout=180):
    """扫描页面并自动保存认证信息"""

    print(f"\n{'='*60}")
    print(f"[INFO] 自动保存认证信息")
    print(f"{'='*60}")
    print(f"目标URL: {url}")
    print(f"认证文件: {auth_file}")
    print(f"等待时间: {timeout}秒")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        # 启动浏览器（有界面模式）
        print("[INFO] 启动浏览器...")
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 导航到目标页面
        print(f"[URL] 正在导航到: {url}")
        page.goto(url)
        time.sleep(2)

        # 检测是否需要登录
        print("\n[CHECK] 检测登录状态...")
        is_login = AuthDetector.is_login_page(page)

        if is_login:
            print("\n[WARNING]  检测到登录页面")
            print("[INFO] 请在浏览器中完成登录操作")
            print("[WAIT] 脚本将自动检测登录状态并保存认证信息\n")

            # 等待登录
            start_time = time.time()
            logged_in = False

            while time.time() - start_time < timeout:
                time.sleep(2)  # 每2秒检查一次

                # 检查是否已登录
                if AuthDetector.is_logged_in(page):
                    print("\n[OK] 检测到登录成功！")
                    logged_in = True
                    break

                elapsed = int(time.time() - start_time)
                remaining = timeout - elapsed
                print(f"\r  [等待] 已等待 {elapsed}秒 / {timeout}秒 (剩余{remaining}秒)     ", end='')

            if not logged_in:
                print(f"\n[ERROR] 等待超时 ({timeout}秒)")
                print("[TIP] 建议:")
                print("   1. 检查网络连接")
                print("   2. 确认登录凭据是否正确")
                print("   3. 尝试增加等待时间")
                browser.close()
                return False
        else:
            print("[OK] 已经登录或无需登录")

        # 等待页面稳定
        print("\n[WAIT] 等待页面稳定 (3秒)...")
        time.sleep(3)

        # 保存认证状态
        print(f"[SAVE] 正在保存认证状态到: {auth_file}")

        # 确保目录存在
        auth_dir = os.path.dirname(auth_file)
        if auth_dir and not os.path.exists(auth_dir):
            os.makedirs(auth_dir, exist_ok=True)

        # 保存存储状态
        context.storage_state(path=auth_file)

        # 验证文件
        if os.path.exists(auth_file):
            file_size = os.path.getsize(auth_file)
            print(f"[OK] 认证状态已保存 (大小: {file_size/1024:.2f} KB)")

            # 读取并显示信息
            with open(auth_file, 'r', encoding='utf-8') as f:
                storage_state = json.load(f)
                cookies_count = len(storage_state.get('cookies', []))
                origins_count = len(storage_state.get('origins', []))
                print(f"   Cookies: {cookies_count}")
                print(f"   Origins: {origins_count}")

            # 关闭浏览器
            print("\n[CLOSE] 关闭浏览器...")
            browser.close()

            return True
        else:
            print("[ERROR] 保存认证状态失败")
            browser.close()
            return False


def main():
    parser = argparse.ArgumentParser(
        description='增强版测试生成 - 自动处理认证',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 交互式生成
  python scripts/generate_test_with_auth.py --interactive

  # 直接生成测试
  python scripts/generate_test_with_auth.py --url https://chat.deepseek.com/ --output tests/chat.spec.js

  # 只保存认证，不生成测试
  python scripts/generate_test_with_auth.py --url https://chat.deepseek.com/ --auth-only
        '''
    )

    parser.add_argument('--url', help='目标URL')
    parser.add_argument('--output', help='输出测试文件路径')
    parser.add_argument('--auth-file', default='auth.json', help='认证文件路径 (默认: auth.json)')
    parser.add_argument('--timeout', type=int, default=180, help='等待登录超时时间(秒) (默认: 180)')
    parser.add_argument('--auth-only', action='store_true', help='只保存认证，不生成测试文件')
    parser.add_argument('--interactive', action='store_true', help='交互式模式')

    args = parser.parse_args()

    # 交互式模式
    if args.interactive:
        print("[TOOL] 交互式模式\n")
        url = input("请输入目标URL: ").strip()
        if not url:
            print("[ERROR] URL不能为空")
            sys.exit(1)

        output_file = input("请输入输出测试文件路径 (可选，按回车跳过): ").strip() or None
        auth_file = input("请输入认证文件路径 (默认: auth.json): ").strip() or 'auth.json'

        timeout_input = input("请输入等待登录超时时间(秒) (默认: 180): ").strip()
        timeout = int(timeout_input) if timeout_input else 180

        auth_only = input("只保存认证？(y/N): ").strip().lower() == 'y'

    else:
        # 命令行模式
        if not args.url:
            print("[ERROR] 错误: 请提供 --url 参数或使用 --interactive")
            parser.print_help()
            sys.exit(1)

        url = args.url
        output_file = args.output
        auth_file = args.auth_file
        timeout = args.timeout
        auth_only = args.auth_only

    # 步骤1: 保存认证
    print("\n" + "="*60)
    print("步骤 1/2: 保存认证信息")
    print("="*60)

    success = scan_and_save_auth(url, auth_file, timeout)

    if not success:
        print("\n[ERROR] 保存认证失败，无法继续")
        sys.exit(1)

    # 步骤2: 生成测试
    if not auth_only:
        if not output_file:
            print("\n[WARNING]  未指定输出文件，跳过测试生成")
            print("[TIP] 使用 --output 参数指定输出文件")
            sys.exit(0)

        print("\n" + "="*60)
        print("步骤 2/2: 生成测试文件")
        print("="*60)

        # 生成测试代码
        test_name = os.path.splitext(os.path.basename(output_file))[0]
        test_code = generate_test_code(url, auth_file, test_name)

        # 保存测试文件
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(test_code)

        print(f"\n[OK] 测试文件已生成: {output_file}")

        # ========== 新增：自动验证步骤 ==========
        print("\n" + "="*60)
        print("步骤 3/3: 自动验证选择器质量")
        print("="*60)

        # 运行静态验证
        print("\n[验证 1/2] 静态验证检查...")
        verify_script = os.path.join(project_root, 'scripts', 'verify_selectors.py')
        result = os.system(f'python "{verify_script}" "{output_file}"')
        if result == 0:
            print("  ✅ 静态验证通过")
        else:
            print("  ⚠️  静态验证发现问题，请查看上述输出")

        # 运行选择器质量评分
        print("\n[验证 2/2] 选择器质量评分...")
        quality_script = os.path.join(project_root, 'scripts', 'analyze_selector_quality.py')
        result = os.system(f'python "{quality_script}" "{output_file}"')
        if result == 0:
            print("  ✅ 选择器质量达标")
        else:
            print("  ⚠️  选择器质量不达标，建议优化")

        # ========== 验证完成 ==========

        # 显示后续步骤
        print("\n" + "="*60)
        print("[INFO] 后续步骤")
        print("="*60)
        print(f"1. 查看生成的测试文件:")
        print(f"   cat {output_file}")
        print(f"\n2. 运行测试:")
        print(f"   npx playwright test {os.path.basename(output_file)} --reporter=html")
        print(f"\n3. 查看测试报告:")
        print(f"   npx playwright show-report")

    print("\n[OK] 完成！")


if __name__ == '__main__':
    main()
