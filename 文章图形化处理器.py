import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests
import json
import os
import graphviz
from PIL import Image, ImageTk
import io

# 初始化主窗口
root = tk.Tk()
root.title("文章图形化处理器")
root.geometry("1200x800")

# 创建左侧输入区
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 主输入框
input_label = tk.Label(left_frame, text="输入文本：")
input_label.pack(fill=tk.X)
input_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD)
input_text.pack(fill=tk.BOTH, expand=True)

# 需求输入框
requirement_label = tk.Label(left_frame, text="格式要求：（如：流程图、思维导图、树形图等）")
requirement_label.pack(fill=tk.X)
requirement_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=8)
requirement_text.pack(fill=tk.BOTH)

# 创建中间按钮区
center_frame = tk.Frame(root)
center_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

# API密钥配置
try:
    key_file = os.path.join(os.path.dirname(__file__), "api.key")
    with open(key_file, "r") as f:
        API_KEY = f.read().strip()
except FileNotFoundError:
    messagebox.showerror("错误", "找不到api.key文件")
    exit()

# DOT生成相关函数
def generate_dot():
    # 获取格式要求
    requirements = requirement_text.get("1.0", tk.END).strip()
    
    # 合并到提示语
    if requirements:
        system_prompt = f"根据以下要求生成规范的DOT脚本:\n{requirements}\n文章内容："
    else:
        system_prompt = "生成规范的DOT脚本描述文章结构"
    text = input_text.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("提示", "请输入文本内容")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": f"严格按照以下要求生成{requirements}的DOT脚本，使用对应图形结构的标准语法"},
            {"role": "user", "content": text}
        ]
    }

    try:
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        dot_script = response.json()["choices"][0]["message"]["content"]
        
        # 提取有效DOT语法部分（参考思维导图生成器v02.py）
        if 'digraph' in dot_script:
            start_index = dot_script.index('digraph')
            end_index = dot_script.rindex('}')
            clean_dot = dot_script[start_index:end_index+1]
            
            # 强制添加字体配置
            if '{' in clean_dot:
                insert_pos = clean_dot.find('{') + 1
                # 已移除重复的字体配置
                clean_dot = clean_dot[:insert_pos] + clean_dot[insert_pos:]
        else:
            clean_dot = f'digraph {{\n    node [fontname="SimHei"];\n    edge [fontname="SimHei"];\n{dot_script}\n}}'
        
        # 添加全局字体声明
        # 已移除多余的全局字体声明
        if '{' in clean_dot:
            insert_pos = clean_dot.find('{') + 1
            font_declaration = '\n    node [fontname="Microsoft YaHei"];\n    edge [fontname="Microsoft YaHei"];\n    graph [fontname="Microsoft YaHei"];'
            clean_dot = clean_dot[:insert_pos] + font_declaration.replace('\\n', '\n') + clean_dot[insert_pos:]
        
        # 验证基本语法结构
        if not clean_dot.startswith(('digraph', 'graph')):
            messagebox.showerror("错误", "生成的DOT脚本格式不正确")
            return
        
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, clean_dot)
    except Exception as e:
        messagebox.showerror("错误", f"API调用失败: {str(e)}")

# 保存DOT函数
def save_dot():
    content = output_text.get("1.0", tk.END)
    if not content.strip():
        messagebox.showwarning("提示", "请先生成DOT脚本")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".dot",
        filetypes=[("DOT文件", "*.dot"), ("所有文件", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", "文件保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

# 思维导图生成函数
def generate_image():
    dot_content = output_text.get("1.0", tk.END)
    if not dot_content.strip():
        messagebox.showwarning("提示", "请先生成DOT脚本")
        return

    try:
        # 使用graphviz渲染
        graph = graphviz.Source(dot_content, encoding='utf-8')
        
        # 保存临时文件
        temp_file = "temp_graph"
        graph.render(temp_file, format='png', cleanup=True)
        
        # 显示预览图片
        img = Image.open(temp_file + ".png")
        img.thumbnail((600, 600))
        photo = ImageTk.PhotoImage(img)
        
        # 创建图片预览窗口
        preview = tk.Toplevel(root)
        preview.title("思维导图预览")
        label = tk.Label(preview, image=photo)
        label.image = photo  # 保持引用
        label.pack()
        
        # 添加保存按钮
        save_img_btn = tk.Button(preview, text="保存图片", 
                               command=lambda: save_image(temp_file + ".png"))
        save_img_btn.pack(pady=10)
    
    except Exception as e:
        messagebox.showerror("错误", f"生成图片失败: {str(e)}")

# 按钮容器
btn_container = tk.Frame(center_frame)
btn_container.pack(pady=20)

# 功能按钮
generate_btn = tk.Button(btn_container, text="生成DOT", width=15, command=generate_dot)
generate_btn.pack(pady=5)
save_btn = tk.Button(btn_container, text="保存DOT", width=15, command=save_dot)
save_btn.pack(pady=5)
generate_image_btn = tk.Button(btn_container, text="生成思维导图", width=15, command=generate_image)
generate_image_btn.pack(pady=5)

# 创建右侧输出区
right_frame = tk.Frame(root)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

output_label = tk.Label(right_frame, text="DOT脚本输出：")
output_label.pack(fill=tk.X)

output_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
output_text.pack(fill=tk.BOTH, expand=True)

# 配置窗口缩放比例
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(2, weight=1)
# API密钥配置
try:
    with open("api.key", "r") as f:
        API_KEY = f.read().strip()
except FileNotFoundError:
    messagebox.showerror("错误", "找不到api.key文件")
    exit()

# DOT生成相关函数
def generate_dot():
    # 获取格式要求
    requirements = requirement_text.get("1.0", tk.END).strip()
    
    # 合并到提示语
    if requirements:
        system_prompt = f"根据以下要求生成规范的DOT脚本:\n{requirements}\n文章内容："
    else:
        system_prompt = "生成规范的DOT脚本描述文章结构"
    text = input_text.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("提示", "请输入文本内容")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": "生成标准的dot脚本"},
            {"role": "user", "content": text}
        ]
    }

    try:
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        dot_script = response.json()["choices"][0]["message"]["content"]
        
        # 提取有效DOT语法部分（参考思维导图生成器v02.py）
        if 'digraph' in dot_script:
            start_index = dot_script.index('digraph')
            end_index = dot_script.rindex('}')
            clean_dot = dot_script[start_index:end_index+1]
            
            # 强制添加字体配置
            if '{' in clean_dot:
                insert_pos = clean_dot.find('{') + 1
                font_config = '\\n    node [fontname=\\"SimHei\\"];\\n    edge [fontname=\\"SimHei\\"];\\n    graph [fontname=\\"SimHei\\"];'
                clean_dot = clean_dot[:insert_pos] + font_config + clean_dot[insert_pos:]
        else:
            clean_dot = f'digraph {{\n    node [fontname="SimHei"];\n    edge [fontname="SimHei"];\n{dot_script}\n}}'
        
        # 添加全局字体声明
        if '{' in clean_dot:
            insert_pos = clean_dot.find('{') + 1
            font_declaration = '\n    node [fontname="SimHei"];\n    edge [fontname="SimHei"];'
            clean_dot = clean_dot[:insert_pos] + font_declaration.replace('\\n', '\n') + clean_dot[insert_pos:]
        
        # 验证基本语法结构
        if not clean_dot.startswith(('digraph', 'graph')):
            messagebox.showerror("错误", "生成的DOT脚本格式不正确")
            return
        
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, clean_dot)
    except Exception as e:
        messagebox.showerror("错误", f"API调用失败: {str(e)}")

# 保存DOT函数
def save_dot():
    content = output_text.get("1.0", tk.END)
    if not content.strip():
        messagebox.showwarning("提示", "请先生成DOT脚本")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".dot",
        filetypes=[("DOT文件", "*.dot"), ("所有文件", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", "文件保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

# 思维导图生成函数
def generate_image():
    dot_content = output_text.get("1.0", tk.END)
    if not dot_content.strip():
        messagebox.showwarning("提示", "请先生成DOT脚本")
        return

    try:
        # 使用graphviz创建Digraph对象
        graph = graphviz.Digraph()
        graph.attr(fontname='SimHei')
        graph.node_attr['fontname'] = 'SimHei'
        graph.edge_attr['fontname'] = 'SimHei'
        
        # 添加DOT内容
        graph.body = dot_content.split('\n')
        
        # 保存临时文件
        temp_file = "temp_graph"
        graph.render(temp_file, format='png', cleanup=True)
        
        # 显示预览图片
        img = Image.open(temp_file + ".png")
        img.thumbnail((600, 600))
        photo = ImageTk.PhotoImage(img)
        
        # 创建图片预览窗口
        preview = tk.Toplevel(root)
        preview.title("图片预览")
        label = tk.Label(preview, image=photo)
        label.image = photo  # 保持引用
        label.pack()
        
        # 添加保存按钮
        save_img_btn = tk.Button(preview, text="保存图片", 
                               command=lambda: save_image(temp_file + ".png"))
        save_img_btn.pack(pady=10)
    
    except Exception as e:
        messagebox.showerror("错误", f"生成图片失败: {str(e)}")

# 图片保存函数
def save_image(source_path):
    dest_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
    )
    if dest_path:
        try:
            with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            messagebox.showinfo("成功", "图片保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

root.mainloop()
