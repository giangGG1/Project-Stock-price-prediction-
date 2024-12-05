import tkinter as tk
from tkinter import filedialog
import os
import subprocess
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk

# Biến toàn cục để lưu đường dẫn file đã chọn
selected_file_path = ""

# Danh sách đường dẫn của các file code (cập nhật đường dẫn chính xác ở đây)
code_paths = [
    "giaodien/test.py", 
    "giaodien/test2.py", 
    "./model3.py", "./model4.py", "./model5.py", 
    "./code6.py", "./code7.py", "./code8.py", 
    "./code9.py", "./code10.py", "./code11.py", 
    "./code12.py", "./code13.py", "./code14.py", 
    "./code15.py"
]
# Biến toàn cục để lưu các đồ thị và kết quả đầu ra
graph_list = []
terminal_list = []

# Hàm để chọn file và cập nhật biến toàn cục selected_file_path
def select_file():
    global selected_file_path
    selected_file_path = filedialog.askopenfilename()  # Mở hộp thoại để chọn file
    if selected_file_path:  # Nếu người dùng đã chọn file
        file_path_label.config(text=f"Selected File: {selected_file_path}")  # Hiển thị đường dẫn của file

        # Cập nhật biến 'path' trong từng file code
        update_code_files()

# Hàm để cập nhật biến 'path' trong từng file code
def update_code_files():
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")

    for rel_path in code_paths:
        abs_path = os.path.abspath(rel_path)
        print(f"Processing file: {abs_path}")  # In ra để kiểm tra đường dẫn

        if os.path.exists(abs_path):
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()

                # Thay thế giá trị của biến 'path' trong code_content
                updated_code_content = code_content.replace('path = ""', f'path = "{selected_file_path}"')

                # Ghi lại nội dung đã cập nhật vào file
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(updated_code_content)

                print(f"Updated {abs_path} with selected file path: {selected_file_path}")
            except UnicodeDecodeError as e:
                print(f"Failed to read file {abs_path} due to encoding error: {e}")
        else:
            print(f"File {abs_path} not found!")

# Hàm để chạy một file code và hiển thị kết quả trong Text widget
def run_code(file_path, output_widget, plot_frame, idx):
    abs_path = os.path.abspath(file_path)
    if os.path.exists(abs_path):
        process = subprocess.Popen(
            ["python", abs_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        def read_output():
            terminal_output = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_widget.insert(tk.END, output)
                    output_widget.see(tk.END)
                    terminal_output.append(output)
            err = process.stderr.read()
            if err:
                output_widget.insert(tk.END, err)
                output_widget.see(tk.END)
                terminal_output.append(err)

            # Lưu kết quả đầu ra vào danh sách
            terminal_list[idx] = ''.join(terminal_output)

            # Hiển thị đồ thị trong plot_frame nếu có
            show_plot(abs_path, plot_frame, idx)

        threading.Thread(target=read_output).start()
    else:
        output_widget.insert(tk.END, f"File {abs_path} not found!\n")
        output_widget.see(tk.END)

# Hàm để hiển thị đồ thị matplotlib trong plot_frame
def show_plot(file_path, plot_frame, idx):
    try:
        fig, ax = plt.subplots()

        # Các dòng code để vẽ đồ thị sẽ được thực thi
        with open(file_path, 'r') as f:
            code_content = f.read()

        # Tạo không gian tên riêng biệt để thực thi code
        local_namespace = {}
        exec(code_content, globals(), local_namespace)

        # Kiểm tra xem có đồ thị nào được tạo ra hay không
        if 'plt' in local_namespace and isinstance(local_namespace['plt'], plt.Figure):
            canvas = FigureCanvasTkAgg(local_namespace['plt'], master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            graph_list[idx] = local_namespace['plt']
        else:
            # Đồ thị rỗng nếu không có đồ thị nào được tạo ra
            graph_list[idx] = None
            print(f"No plot created for {file_path}")

    except Exception as e:
        print(f"Failed to display plot for {file_path}: {e}")
        graph_list[idx] = None

# Tạo cửa sổ chính của ứng dụng
root = tk.Tk()
root.title("File Selector")



# Button để chọn file
select_file_button = tk.Button(root, text="Select File", command=select_file)
select_file_button.pack(pady=10)

# Label để hiển thị đường dẫn của file đã chọn
file_path_label = tk.Label(root, text="Selected File: None")
file_path_label.pack(pady=10)

# Tạo một canvas với scrollbar để chứa các frames
canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Tạo danh sách để lưu các Text widget và Frame cho từng file code
output_widgets = []
plot_frames = []

# Tạo các nút cho từng file code và các Text widget
for idx, file_path in enumerate(code_paths):
    frame_code = tk.Frame(scrollable_frame, borderwidth=2, relief="sunken")
    frame_code.pack(side="top", fill="x", padx=5, pady=5)

    file_label = tk.Label(frame_code, text=f"File: {file_path}")
    file_label.pack(side="top", padx=10)

    # Tạo frame để chứa đồ thị (70%) và kết quả terminal (30%)
    plot_frame = tk.Frame(frame_code, width=700, height=300)
    plot_frame.pack_propagate(False)  # Ngăn frame thay đổi kích thước theo nội dung
    plot_frame.pack(side="left", padx=5, pady=5, fill="both", expand=True)

    # Tạo Text widget để hiển thị kết quả
    output_widget = tk.Text(frame_code, height=10, width=50)
    output_widget.pack(side="right", padx=10, pady=10, fill="both", expand=True)

    # Tạo nút để chạy file code
    run_button = tk.Button(frame_code, text="Run", command=lambda path=file_path, widget=output_widget, plot=plot_frame, i=idx: run_code(path, widget, plot, i))
    run_button.pack(side="bottom", padx=10)

    output_widgets.append(output_widget)
    plot_frames.append(plot_frame)

    # Khởi tạo các phần tử trong danh sách đồ thị và terminal
    graph_list.append(None)
    terminal_list.append("")

# Chạy tất cả các file code
def run_all():
    for i, file_path in enumerate(code_paths):
        run_code(file_path, output_widgets[i], plot_frames[i], i)

# Nút để chạy tất cả các file code
run_all_button = tk.Button(root, text="Run All", command=run_all)
run_all_button.pack(pady=10)

# Chạy ứng dụng
root.mainloop()

# Sau khi người dùng đã chọn file và thoát khỏi ứng dụng, bạn có thể sử dụng biến selected_file_path để thực hiện các tác vụ tiếp theo
print("Selected file path:", selected_file_path)
