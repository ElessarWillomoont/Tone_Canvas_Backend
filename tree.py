import os
import fnmatch

def load_gitignore_rules(gitignore_path):
    """读取 .gitignore 文件中的规则并提供详细日志"""
    rules = []

    # 检查 .gitignore 文件是否存在
    if not os.path.exists(gitignore_path):
        print(f"[INFO] .gitignore 文件未找到: {gitignore_path}")
        return rules

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过注释和空行
                    if line.endswith('/'):
                        line = line.rstrip('/') + os.sep  # 标记为目录规则
                    rules.append(line)
                    print(f"[INFO] 读取规则: 行 {line_number} -> {line}")
    except PermissionError:
        print(f"[ERROR] 无法读取 .gitignore 文件: 没有权限")
    except Exception as e:
        print(f"[ERROR] 读取 .gitignore 文件时出现错误: {e}")
    else:
        if not rules:
            print(f"[INFO] .gitignore 文件存在，但内容为空或没有有效规则")

    return rules

def is_ignored(path, rules, base_path, ignore_project_files, current_script, generated_files):
    """检查文件或目录是否被忽略"""
    # 默认忽略隐藏文件夹和 `.git`
    default_ignored = ['.git', '.git/*', '.*', '*/.*']

    # 默认忽略的非文本文件扩展名
    non_text_file_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
                                 '.svg', '.tiff', '.webp', '.mp4', '.mp3', '.wav',
                                 '.avi', '.mkv', '.mov', '.zip', '.rar', '.7z',
                                 '.tar', '.gz', '.exe', '.dll', '.iso', '.bin', '.woff',
                                 '.Pitch','.wav',]

    # 常见项目配置文件
    common_project_files = ['next.config.mjs', 'package-lock.json', 'package.json',
                            'README.md', 'tsconfig.json']

    # 归一化路径
    relative_path = os.path.relpath(path, base_path)
    normalized_path = os.path.normpath(relative_path)

    # 检查是否匹配默认规则
    for rule in default_ignored:
        if fnmatch.fnmatch(normalized_path, rule):
            print(f"[DEBUG] 默认忽略: 路径 '{normalized_path}' 匹配规则 '{rule}'")
            return True

    # 检查是否匹配非文本文件扩展名
    if any(normalized_path.endswith(ext) for ext in non_text_file_extensions):
        print(f"[DEBUG] 默认忽略: 路径 '{normalized_path}' 是非文本文件")
        return True

    # 检查是否匹配常见项目配置文件
    if ignore_project_files and os.path.basename(normalized_path) in common_project_files:
        print(f"[DEBUG] 默认忽略: 路径 '{normalized_path}' 是常见项目配置文件")
        return True

    # 检查是否为当前脚本或生成的文件
    if os.path.basename(normalized_path) == current_script or os.path.basename(normalized_path) in generated_files:
        print(f"[DEBUG] 默认忽略: 路径 '{normalized_path}' 是当前脚本或生成文件")
        return True

    # 检查是否匹配 .gitignore 规则
    for rule in rules:
        if rule.startswith('/'):  # 根目录规则
            root_rule = rule.lstrip('/')
            if normalized_path == root_rule or normalized_path.startswith(root_rule + os.sep):
                print(f"[DEBUG] 忽略匹配: 根路径 '{normalized_path}' 匹配规则 '{rule}'")
                return True
        elif rule.endswith(os.sep):  # 目录规则
            if normalized_path.startswith(rule.rstrip(os.sep) + os.sep):
                print(f"[DEBUG] 忽略匹配: 路径 '{normalized_path}' 位于规则 '{rule}' 的子路径")
                return True
        else:  # 全局规则
            if fnmatch.fnmatch(normalized_path, rule):
                print(f"[DEBUG] 忽略匹配: 路径 '{normalized_path}' 匹配规则 '{rule}'")
                return True

    return False

def generate_file_tree(base_path, rules, ignore_project_files, current_script, generated_files):
    """生成项目文件树"""
    result = []
    for root, dirs, files in os.walk(base_path):
        # 过滤掉被忽略的目录
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), rules, base_path, ignore_project_files, current_script, generated_files)]

        # 记录当前目录
        indent = '  ' * (root.count(os.sep) - base_path.count(os.sep))
        result.append(f"{indent}[{os.path.basename(root) if root != base_path else '.'}]")

        # 记录文件
        for file in files:
            file_path = os.path.join(root, file)
            if not is_ignored(file_path, rules, base_path, ignore_project_files, current_script, generated_files):
                result.append(f"{indent}  {file}")
    
    return '\n'.join(result)

def generate_structure_with_content(base_path, rules, ignore_project_files, current_script, generated_files):
    """生成项目结构和文件内容"""
    result = []

    for root, dirs, files in os.walk(base_path):
        # 过滤掉被忽略的目录
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), rules, base_path, ignore_project_files, current_script, generated_files)]

        # 记录当前目录
        indent = '  ' * (root.count(os.sep) - base_path.count(os.sep))
        result.append(f"{indent}[{os.path.basename(root) if root != base_path else '.'}]")

        # 记录文件
        for file in files:
            file_path = os.path.join(root, file)
            if not is_ignored(file_path, rules, base_path, ignore_project_files, current_script, generated_files):
                result.append(f"{indent}  {file}")
                # 添加文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        file_indent = '    ' + indent
                        result.append(f"{file_indent}--- File Content ---")
                        result.extend([f"{file_indent}{line}" for line in content.splitlines()])
                        result.append(f"{file_indent}--- End of File ---")
                except Exception as e:
                    print(f"[WARNING] 无法读取文件内容: {file_path}, 错误: {e}")
    
    return '\n'.join(result)

def main():
    base_path = '.'  # 项目根目录
    gitignore_path = os.path.join(base_path, '.gitignore')

    # 获取当前脚本文件名和生成的文件名
    current_script = os.path.basename(__file__)
    generated_files = ['project_structure.txt']

    # 用户选项：是否忽略常见项目配置文件
    user_input = input("是否忽略常见项目配置文件（如 package.json 等）？(Y/n): ").strip().lower()
    ignore_project_files = user_input in ['y', 'yes', '']

    # 加载 .gitignore 规则
    print("[INFO] 开始加载 .gitignore 文件...")
    rules = load_gitignore_rules(gitignore_path)

    # 检查是否加载了任何规则
    if not rules:
        print("[INFO] 没有加载到有效的 .gitignore 规则，可能导致结果不符合预期")

    # 生成文件树
    print("[INFO] 正在生成文件树...")
    file_tree = generate_file_tree(base_path, rules, ignore_project_files, current_script, generated_files)

    # 生成文件树和内容
    print("[INFO] 正在生成文件结构和内容...")
    structure_with_content = generate_structure_with_content(base_path, rules, ignore_project_files, current_script, generated_files)

    # 将结果保存到文件
    output_file = 'project_structure.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("--- Project File Tree ---\n")
        f.write(file_tree + '\n\n')
        f.write("--- Project File Tree with Content ---\n")
        f.write(structure_with_content)
    
    print(f"[INFO] 项目结构已保存到 {output_file}")

if __name__ == "__main__":
    main()
