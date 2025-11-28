from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import mysql.connector
import datetime
from tkinter import filedialog  
import mysql.connector
import pandas as pd 

# ====== Hàm trợ giúp định dạng tiền tệ ======
def format_currency(value):
    if isinstance(value, (int, float)):
        # Chuyển đổi sang string, thêm dấu phân cách hàng nghìn, rồi thay dấu phẩy bằng dấu chấm
        return f"{int(value):,}".replace(",", ".")
    elif isinstance(value, str):
        try:
            # Loại bỏ dấu chấm phân cách hàng nghìn (nếu có) trước khi chuyển đổi
            value = int(value.replace('.', ''))
            return f"{value:,}".replace(",", ".")
        except ValueError:
            return value # Return as is if conversion fails
    return value

def unformat_currency(formatted_value):
    if isinstance(formatted_value, str):
        try:
            # Loại bỏ dấu chấm và chuyển đổi thành số nguyên
            return int(formatted_value.replace('.', '').replace(',', ''))
        except ValueError:
            return 0 # Trả về 0 nếu không thể chuyển đổi
    return formatted_value

# ====== Hàm căn giữa cửa sổ ======
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

# ====== Kết nối MySQL ======
def connect_db():
    """Kết nối tới cơ sở dữ liệu qlbanhang."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="qlbanhang"
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Lỗi kết nối CSDL", f"Không thể kết nối MySQL: {err}")
        return None

# ===== HÀM KHO VÀ QUẢN LÝ THIẾT BỊ =====
def show_product_list(product_type, brand_name, parent_menu_window):
    """
    Hiển thị danh sách sản phẩm tổng hợp theo Loại sản phẩm và Hãng đã chọn,
    kèm theo Số lượng tồn kho. (Dành cho giao diện Kho)
    """
    prod_list_window = Toplevel(root)
    prod_list_window.title(f"Tồn kho: {product_type} - Hãng {brand_name}")
    center_window(prod_list_window, 850, 450) # Căn giữa cửa sổ
    prod_list_window.configure(bg='#f7f7f7')

    def go_back_to_menu():
        prod_list_window.destroy()
        parent_menu_window.deiconify()

    Label(prod_list_window, 
          text=f"TỒN KHO: {product_type} ({brand_name})", 
          font=("Arial", 18, "bold"), 
          fg='#1A237E', 
          bg='#f7f7f7').pack(pady=20)

    list_frame = Frame(prod_list_window, padx=20, bg='#f7f7f7')
    list_frame.pack(pady=10, fill='both', expand=True)

    columns = ("Tên", "Giá tiền (VND)", "Ngày nhập gần nhất", "Số lượng")
    tree = ttk.Treeview(list_frame, columns=columns, show='headings')

    tree.heading("Tên", text="Tên sản phẩm", anchor=W)
    tree.heading("Giá tiền (VND)", text="Giá tiền", anchor=E)
    tree.heading("Ngày nhập gần nhất", text="Nhập gần nhất", anchor=CENTER)
    tree.heading("Số lượng", text="Số lượng", anchor=CENTER)

    tree.column("Tên", width=350, anchor=W)
    tree.column("Giá tiền (VND)", width=150, anchor=E)
    tree.column("Ngày nhập gần nhất", width=150, anchor=CENTER)
    tree.column("Số lượng", width=100, anchor=CENTER)

    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill='both', expand=True)
    
    def load_filtered_data():
        conn = connect_db()
        if not conn: return
        try:
            for i in tree.get_children():
                tree.delete(i)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    TenSP, 
                    GiaTien, 
                    MAX(NgayNhap) AS NgayNhapGanNhat,
                    COUNT(MaSP) AS SoLuong
                FROM 
                    kho 
                WHERE 
                    LoaiSP=%s AND Hang=%s
                GROUP BY
                    TenSP, GiaTien
                ORDER BY
                    TenSP
            """
            cur.execute(query, (product_type, brand_name))
            
            rows = cur.fetchall()
            for row in rows:
                formatted_row = list(row)
                formatted_row[1] = format_currency(row[1])
                tree.insert("", END, values=formatted_row)
            
            if not rows:
                Label(list_frame, 
                      text="Loại thiết bị này đã hết hàng !!!", 
                      fg='red', 
                      bg='#f7f7f7', 
                      font=("Arial", 16, 'bold')).pack(pady=20) 
                tree.pack_forget()
            else:
                tree.pack(side="left", fill='both', expand=True) 

        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu", f"Lỗi truy vấn CSDL: {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()

    load_filtered_data()

    Button(prod_list_window, 
           text="< Trở lại Menu Sản phẩm", 
           width=30, 
           height=1, 
           bg="#546E7A", 
           fg='white',
           font=("Arial", 10, 'bold'),
           command=go_back_to_menu).pack(pady=20)

def show_category(title, items, previous_window):
    """Hiển thị danh sách các hãng theo loại sản phẩm."""
    previous_window.withdraw()

    new_window = Toplevel(root)
    new_window.title(title)
    center_window(new_window, 400, 450) # Căn giữa cửa sổ
    new_window.configure(bg='#e0f7fa')
    
    def go_back():
        new_window.destroy()
        previous_window.deiconify()

    Label(new_window, text=title, font=("Arial", 16, "bold"), fg='#00796b', bg='#e0f7fa').pack(pady=20)

    frame_btns = Frame(new_window, bg='#e0f7fa')
    frame_btns.pack(pady=10)

    def select_brand_and_show_list(brand_name, product_type, parent_menu_window):
        new_window.destroy()
        show_product_list(product_type, brand_name, parent_menu_window)

    for item in items:
        Button(frame_btns,
               text=item,
               width=20,
               height=2,
               bg="#4db6ac",
               fg="white",
               font=("Arial", 10, 'bold'),
               command=lambda brand=item, type=title, parent=previous_window: select_brand_and_show_list(brand, type, parent)).pack(pady=5)
    
    Button(new_window, 
           text="< Trở lại Menu Sản phẩm", 
           width=25, 
           height=1, 
           bg="#B0BEC5", 
           fg='black',
           font=("Arial", 10, 'bold'),
           command=go_back).pack(pady=20)

def open_menu(parent_window): 
    """Mở cửa sổ menu lựa chọn loại sản phẩm (Dành cho Kho)."""
    menu_window = Toplevel(root)
    menu_window.title("Menu Sản Phẩm (Kho)")
    center_window(menu_window, 400, 450) # Căn giữa cửa sổ
    menu_window.configure(bg='#fff3e0')

    def go_back_to_parent():
        menu_window.destroy()
        parent_window.deiconify()

    Label(menu_window, text="Chọn loại sản phẩm", font=("Arial", 16, "bold"), fg='#ff8f00', bg='#fff3e0').pack(pady=20)

    Button(menu_window, text="Laptop", width=20, height=2, bg="#ffb74d", fg='black',
           command=lambda: show_category("Laptop", ["Dell", "Asus", "MSI", "HP", "Acer","LG","Apple", "Lenovo" ], menu_window)).pack(pady=5)

    Button(menu_window, text="Tablet", width=20, height=2, bg="#aed581", fg='black',
           command=lambda: show_category("Tablet", ["Apple", "Samsung", "Xiaomi","Amazon","Microsoft"], menu_window)).pack(pady=5)

    Button(menu_window, text="Smart Phone", width=20, height=2, bg="#fff176", fg='black',
           command=lambda: show_category("Smart Phone", ["Apple", "Xiaomi", "Samsung", "Realme", "Nokia", "Honor", "OPPO", "Vivo","Google"], menu_window)).pack(pady=5)
    
    Button(menu_window, 
           text="< Trở lại", 
           width=25, 
           height=1, 
           bg="#B0BEC5", 
           fg='black',
           font=("Arial", 10, 'bold'),
           command=go_back_to_parent).pack(pady=20)

def open_employee_management_window():
    """Mở cửa sổ quản lý thiết bị, bao gồm CRUD functions."""
    emp_window = Toplevel(root)
    emp_window.title("Quản lý thiết bị")
    center_window(emp_window, 850, 650) # Căn giữa cửa sổ
    emp_window.configure(bg='#f0f0f0')

    def go_back_to_main():
        emp_window.destroy()
        root.deiconify()
    def clear_input():
        var_MaSP.set("")
        var_TenSP.set("") 
        var_Hang.set("")
        var_GiaTien.set("")
        var_NgayNhap.set(datetime.date.today().strftime("%Y-%m-%d"))
        var_LoaiSP.set(loai_options[0])
        entry_masp.config(state='normal')

    def load_data():
        conn = connect_db()
        if not conn: return
        try:
            for i in tree.get_children(): tree.delete(i)
            cur = conn.cursor()
            cur.execute("SELECT MaSP, TenSP, LoaiSP, Hang, GiaTien, NgayNhap FROM kho ORDER BY MaSP")
            
            for row in cur.fetchall():
                formatted_row = list(row)
                formatted_row[4] = format_currency(row[4])
                tree.insert("", END, values=formatted_row)
        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu", str(e))
        finally: 
            if conn and conn.is_connected():
                conn.close()

    def them_sp():
        MaSP = var_MaSP.get().strip()
        TenSP = var_TenSP.get().strip() 
        NgayNhap = var_NgayNhap.get().strip()
        LoaiSP = var_LoaiSP.get().strip()
        Hang = var_Hang.get().strip()
        GiaTien = var_GiaTien.get().strip().replace('.', '')

        if not all([MaSP, TenSP, NgayNhap, LoaiSP, Hang, GiaTien]):
            messagebox.showwarning("Thiếu thông tin", "Vui lòng điền đầy đủ tất cả các trường.")
            return

        conn = connect_db()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO kho (MaSP, TenSP, LoaiSP, Hang, GiaTien, NgayNhap) VALUES (%s, %s, %s, %s, %s, %s)",
                         (MaSP, TenSP, LoaiSP, Hang, GiaTien, NgayNhap)) 
            conn.commit()
            messagebox.showinfo("Thành công", "Thêm sản phẩm thành công.")
            load_data()
            clear_input()
        except mysql.connector.Error as e:
             messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm sản phẩm: {e}")
        except Exception as e:
             messagebox.showerror("Lỗi", str(e))
        finally: 
            if conn and conn.is_connected():
                conn.close()

    def xoa_sp():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Hãy chọn sản phẩm để xóa.")
            return

        MaSP_to_delete = tree.item(selected)["values"][0]
        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa sản phẩm có mã {MaSP_to_delete} không?"):
            return

        conn = connect_db()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM kho WHERE MaSP=%s", (MaSP_to_delete,))
            conn.commit()
            messagebox.showinfo("Thành công", "Xóa sản phẩm thành công.")
            load_data()
            clear_input()
        except mysql.connector.Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa sản phẩm: {e}")
        finally: 
            if conn and conn.is_connected():
                conn.close()

    def sua_sp_select(event):
        clear_input()
        selected = tree.selection()
        if not selected: return

        values = tree.item(selected[0], 'values')

        MaSP_original = values[0]
        conn = connect_db()
        original_giatien = values[4].replace('.', '').replace(',', '')
        if conn:
            try:
                cur = conn.cursor()
                # Truy vấn lại giá tiền gốc (số) từ DB để tránh lỗi định dạng
                cur.execute("SELECT GiaTien FROM kho WHERE MaSP=%s", (MaSP_original,))
                fetch_result = cur.fetchone()
                if fetch_result:
                     original_giatien = str(fetch_result[0])
            except Exception:
                pass
            finally: 
                if conn and conn.is_connected():
                    conn.close()

        var_MaSP.set(values[0])
        var_TenSP.set(values[1])  
        var_LoaiSP.set(values[2])
        var_Hang.set(values[3])
        var_GiaTien.set(original_giatien)
        var_NgayNhap.set(values[5])

        entry_masp.config(state='readonly')

    def luu_sp():
        MaSP = var_MaSP.get().strip()
        TenSP = var_TenSP.get().strip() 
        NgayNhap = var_NgayNhap.get().strip()
        LoaiSP = var_LoaiSP.get().strip()
        Hang = var_Hang.get().strip()
        GiaTien = var_GiaTien.get().strip().replace('.', '')

        if not MaSP or entry_masp.cget('state') == 'normal':
            messagebox.showwarning("Chưa chọn", "Hãy chọn sản phẩm cần Sửa trước khi Lưu.")
            return

        conn = connect_db()
        if not conn: return
        try:
            cur = conn.cursor()
            # 1. Cập nhật thông tin chi tiết (trừ GiaTien) cho MaSP đang chọn
            cur.execute("""UPDATE kho SET TenSP=%s, NgayNhap=%s,
                            LoaiSP=%s, Hang=%s
                            WHERE MaSP=%s""",
                        (TenSP, NgayNhap, LoaiSP, Hang, MaSP)) 
            
            # 2. Cập nhật GiaTien cho TẤT CẢ các sản phẩm có cùng TenSP
            cur.execute("""UPDATE kho SET GiaTien=%s
                            WHERE TenSP=%s""",
                        (GiaTien, TenSP))
            
            conn.commit()
            messagebox.showinfo("Thành công", f"Cập nhật sản phẩm có mã {MaSP} và ĐÃ ĐỒNG BỘ giá tiền ({format_currency(GiaTien)} VND) cho tất cả sản phẩm cùng tên '{TenSP}' thành công.")
            load_data()
            clear_input()
        except mysql.connector.Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật sản phẩm: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
        finally: 
            if conn and conn.is_connected():
                conn.close()

    Label(emp_window, text="QUẢN LÝ THIẾT BỊ", font=("Arial", 24, "bold"), fg='#004d99', bg='#f0f0f0').pack(pady=20)

    input_frame = Frame(emp_window, bg='#f0f0f0')
    input_frame.pack(padx=30, pady=10, fill='x')

    var_MaSP = StringVar()
    var_TenSP = StringVar() 
    var_LoaiSP = StringVar(emp_window, value="Smart Phone")
    var_Hang = StringVar()
    var_GiaTien = StringVar()
    var_NgayNhap = StringVar(emp_window, value=datetime.date.today().strftime("%Y-%m-%d"))

    col1_frame = Frame(input_frame, bg='#f0f0f0'); col1_frame.pack(side=LEFT, padx=50, expand=True)
    Frame_MaSP = Frame(col1_frame, bg='#f0f0f0'); Frame_MaSP.pack(fill='x', pady=5)
    Label(Frame_MaSP, text="Mã sản phẩm", width=12, anchor='w', bg='#f0f0f0', font=("Arial", 10, 'bold')).pack(side=LEFT)
    entry_masp = Entry(Frame_MaSP, width=25, bd=2, relief=SUNKEN, textvariable=var_MaSP); entry_masp.pack(side=RIGHT)

    Frame_LoaiSP = Frame(col1_frame, bg='#f0f0f0'); Frame_LoaiSP.pack(fill='x', pady=5)
    Label(Frame_LoaiSP, text="Loại sản phẩm", width=12, anchor='w', bg='#f0f0f0', font=("Arial", 10, 'bold')).pack(side=LEFT)
    loai_options = ["Smart Phone", "Laptop", "Tablet"]
    cbb_loaisp = ttk.Combobox(Frame_LoaiSP, textvariable=var_LoaiSP, values=loai_options, state="readonly", width=22); cbb_loaisp.pack(side=RIGHT)

    Frame_TenSP = Frame(col1_frame, bg='#f0f0f0'); Frame_TenSP.pack(fill='x', pady=5)
    Label(Frame_TenSP, text="Tên sản phẩm", width=12, anchor='w', bg='#f0f0f0', font=("Arial", 10, 'bold')).pack(side=LEFT)
    entry_tensp = Entry(Frame_TenSP, width=25, bd=2, relief=SUNKEN, textvariable=var_TenSP); entry_tensp.pack(side=RIGHT)

    col2_frame = Frame(input_frame, bg='#f0f0f0'); col2_frame.pack(side=LEFT, padx=50, expand=True)
    Frame_Hang = Frame(col2_frame, bg='#f0f0f0'); Frame_Hang.pack(fill='x', pady=5)
    Label(Frame_Hang, text="Hãng", width=10, anchor='w', bg='#f0f0f0', font=("Arial", 10, 'bold')).pack(side=LEFT)
    entry_hang = Entry(Frame_Hang, width=25, bd=2, relief=SUNKEN, textvariable=var_Hang); entry_hang.pack(side=RIGHT)

    Frame_GiaTien = Frame(col2_frame, bg='#f0f0f0'); Frame_GiaTien.pack(fill='x', pady=5)
    Label(Frame_GiaTien, text="Giá tiền (VND)", width=15, anchor='w', bg='#f0f0f0', font=("Arial", 10, 'bold')).pack(side=LEFT)
    entry_giatien = Entry(Frame_GiaTien, width=25, bd=2, relief=SUNKEN, textvariable=var_GiaTien); entry_giatien.pack(side=RIGHT)

    Frame_NgayNhap = Frame(col2_frame, bg='#f0f0f0'); Frame_NgayNhap.pack(fill='x', pady=5)
    Label(Frame_NgayNhap, text="Ngày nhập", width=10, anchor='w', bg='#f0f0f0', font=("Arial", 10, 'bold')).pack(side=LEFT)
    entry_ngaynhap = Entry(Frame_NgayNhap, width=25, bd=2, relief=SUNKEN, textvariable=var_NgayNhap); entry_ngaynhap.pack(side=RIGHT)

    Label(emp_window, text="Danh sách thiết bị", font=("Arial", 14, "bold"), bg='#f0f0f0').pack(padx=30, pady=(20, 10), anchor='w')

    list_frame = Frame(emp_window, padx=30, bg='#f0f0f0'); list_frame.pack(pady=5, fill='both', expand=True)

    columns = ("Mã sp", "Tên", "Loại sp", "Hãng", "Giá tiền (VND)", "Ngày nhập")
    tree = ttk.Treeview(list_frame, columns=columns, show='headings')

    for col in columns: tree.heading(col, text=col, anchor=CENTER)
    tree.column("Mã sp", width=70, anchor=CENTER)
    tree.column("Tên", width=150, anchor=W)
    tree.column("Loại sp", width=100, anchor=CENTER)
    tree.column("Hãng", width=100, anchor=CENTER)
    tree.column("Giá tiền (VND)", width=120, anchor=E)
    tree.column("Ngày nhập", width=90, anchor=CENTER)
    tree.pack(fill='both', expand=True)

    tree.bind('<<TreeviewSelect>>', sua_sp_select)
    load_data()

    button_frame = Frame(emp_window, bg='#f0f0f0'); button_frame.pack(pady=30)
    btn_style = {'width': 12, 'height': 1, 'bd': 3, 'relief': RAISED, 'font': ("Arial", 10, 'bold'), 'fg': 'white'}
    
    Button(button_frame, text="Tìm kiếm", bg='#FFC107', 
           command=lambda: [emp_window.withdraw(), open_menu(emp_window)], 
           **btn_style).pack(side=LEFT, padx=8) 

    Button(button_frame, text="Thêm", bg='#4CAF50', command=them_sp, **btn_style).pack(side=LEFT, padx=8)
    Button(button_frame, text="Sửa", bg='#008CBA', command=luu_sp, **btn_style).pack(side=LEFT, padx=8)
    Button(button_frame, text="Xóa", bg='#9C27B0', command=xoa_sp, **btn_style).pack(side=LEFT, padx=8)
    Button(button_frame, text="Trở lại", bg='#607D8B', command=go_back_to_main, **btn_style).pack(side=LEFT, padx=8)

# ===== HÀM HỖ TRỢ CHỌN SẢN PHẨM CHO GIAO DIỆN BÁN HÀNG =====

def open_selection_menu(sales_window, detail_tree):
    menu_window = Toplevel(root)
    menu_window.title("Chọn Loại Sản Phẩm (Bán hàng)")
    center_window(menu_window, 400, 450) # Căn giữa cửa sổ
    menu_window.configure(bg='#fff3e0')

    def go_back_to_sales():
        menu_window.destroy()
        sales_window.deiconify()

    Label(menu_window, text="Chọn loại sản phẩm", font=("Arial", 16, "bold"), fg='#ff8f00', bg='#fff3e0').pack(pady=20)
    
    Button(menu_window, text="Laptop", width=20, height=2, bg="#ffb74d", fg='black',
           command=lambda: show_selection_category("Laptop", ["Dell", "Asus", "MSI", "HP", "Acer","LG","Apple", "Lenovo" ], menu_window, sales_window, detail_tree)).pack(pady=5)

    Button(menu_window, text="Tablet", width=20, height=2, bg="#aed581", fg='black',
           command=lambda: show_selection_category("Tablet", ["Apple", "Samsung", "Xiaomi","Amazon","Microsoft"], menu_window, sales_window, detail_tree)).pack(pady=5)

    Button(menu_window, text="Smart Phone", width=20, height=2, bg="#fff176", fg='black',
           command=lambda: show_selection_category("Smart Phone", ["Apple", "Xiaomi", "Samsung", "Realme", "Nokia", "Honor", "OPPO", "Vivo","Google"], menu_window, sales_window, detail_tree)).pack(pady=5)
    
    Button(menu_window, 
           text="< Trở lại Bán hàng", 
           width=25, 
           height=1, 
           bg="#B0BEC5", 
           fg='black',
           font=("Arial", 10, 'bold'),
           command=go_back_to_sales).pack(pady=20)


def show_selection_category(title, items, previous_window, sales_window, detail_tree):
    previous_window.withdraw()

    new_window = Toplevel(root)
    new_window.title(f"Chọn Hãng: {title}")
    center_window(new_window, 400, 450) # Căn giữa cửa sổ
    new_window.configure(bg='#e0f7fa')
    
    def go_back():
        new_window.destroy()
        previous_window.deiconify()

    Label(new_window, text=f"Chọn Hãng: {title}", font=("Arial", 16, "bold"), fg='#00796b', bg='#e0f7fa').pack(pady=20)

    frame_btns = Frame(new_window, bg='#e0f7fa'); frame_btns.pack(pady=10)

    def select_brand_and_show_list(brand_name, product_type, parent_menu_window, sales_window, detail_tree):
        new_window.destroy()
        show_selection_list_for_sales(product_type, brand_name, parent_menu_window, sales_window, detail_tree)

    for item in items:
        Button(frame_btns,
               text=item,
               width=20,
               height=2,
               bg="#4db6ac",
               fg="white",
               font=("Arial", 10, 'bold'),
               command=lambda brand=item, type=title, parent=previous_window: select_brand_and_show_list(brand, type, parent, sales_window, detail_tree)).pack(pady=5)
    
    Button(new_window, 
           text="< Trở lại Menu Sản phẩm", 
           width=25, 
           height=1, 
           bg="#B0BEC5", 
           fg='black',
           font=("Arial", 10, 'bold'),
           command=go_back).pack(pady=20)


def show_selection_list_for_sales(product_type, brand_name, parent_menu_window, sales_window, detail_tree):
    select_window = Toplevel(root)
    select_window.title(f"Chọn Sản phẩm: {product_type} - Hãng {brand_name}")
    center_window(select_window, 850, 450) # Căn giữa cửa sổ
    select_window.configure(bg='#f7f7f7')
    
    Label(select_window, 
          text=f"CHỌN SẢN PHẨM: {product_type} ({brand_name})", 
          font=("Arial", 18, "bold"), 
          fg='#1A237E', 
          bg='#f7f7f7').pack(pady=20)

    list_frame = Frame(select_window, padx=20, bg='#f7f7f7'); list_frame.pack(pady=10, fill='both', expand=True)

    columns = ("Tên", "Giá tiền (VND)", "Ngày nhập gần nhất", "Số lượng tồn")
    tree = ttk.Treeview(list_frame, columns=columns, show='headings')

    tree.heading("Tên", text="Tên sản phẩm", anchor=W); tree.heading("Giá tiền (VND)", text="Giá tiền", anchor=E)
    tree.heading("Ngày nhập gần nhất", text="Nhập gần nhất", anchor=CENTER); tree.heading("Số lượng tồn", text="Tồn", anchor=CENTER) 

    tree.column("Tên", width=350, anchor=W); tree.column("Giá tiền (VND)", width=150, anchor=E)
    tree.column("Ngày nhập gần nhất", width=150, anchor=CENTER); tree.column("Số lượng tồn", width=100, anchor=CENTER) 

    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y"); tree.pack(side="left", fill='both', expand=True)
    
    def load_filtered_data():
        conn = connect_db()
        if not conn: return
        try:
            for i in tree.get_children(): tree.delete(i)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    TenSP, 
                    GiaTien, 
                    MAX(NgayNhap) AS NgayNhapGanNhat,
                    COUNT(MaSP) AS SoLuong
                FROM 
                    kho 
                WHERE 
                    LoaiSP=%s AND Hang=%s
                GROUP BY
                    TenSP, GiaTien
                ORDER BY
                    TenSP
            """
            cur.execute(query, (product_type, brand_name))
            
            rows = cur.fetchall()
            for row in rows:
                formatted_row = list(row)
                formatted_row[1] = format_currency(row[1])
                tree.insert("", END, values=formatted_row)
            
            if not rows:
                Label(list_frame, text="Loại thiết bị này đã hết hàng !!!", fg='red', bg='#f7f7f7', font=("Arial", 16, 'bold')).pack(pady=20) 
                tree.pack_forget()
            else:
                tree.pack(side="left", fill='both', expand=True) 

        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu", f"Lỗi truy vấn CSDL: {e}")
        finally: 
            if conn and conn.is_connected():
                conn.close()

    load_filtered_data()
    
    def add_selected_product_to_order():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một sản phẩm để thêm vào đơn hàng.")
            return

        values = tree.item(selected_item, 'values')
        
        product_name = values[0]
        quantity = 1 
        
        original_price = 0
        try:
            conn = connect_db()
            if not conn: return
            cur = conn.cursor()
            # Lấy giá tiền gốc không định dạng từ DB
            cur.execute("SELECT GiaTien FROM kho WHERE TenSP=%s LIMIT 1", (product_name,))
            fetch_result = cur.fetchone()
            if fetch_result:
                original_price = int(fetch_result[0])
            conn.close()
        except Exception:
            messagebox.showerror("Lỗi", "Không thể lấy giá tiền gốc của sản phẩm.")
            return

        total_price = original_price * quantity
        
        if int(values[3]) < quantity:
            messagebox.showerror("Hết hàng", f"Sản phẩm {product_name} chỉ còn {values[3]} cái.")
            return
            
        # Kiểm tra nếu sản phẩm đã có trong đơn hàng thì tăng số lượng
        for item_id in detail_tree.get_children():
            item_values = detail_tree.item(item_id, 'values')
            if item_values[0] == product_name:
                current_qty = int(item_values[2])
                new_qty = current_qty + quantity
                if int(values[3]) < new_qty:
                    messagebox.showerror("Hết hàng", f"Sản phẩm {product_name} chỉ còn {values[3]} cái. Không thể thêm nữa.")
                    return
                
                new_total = original_price * new_qty
                detail_tree.item(item_id, values=(
                    product_name,
                    format_currency(original_price),
                    new_qty,
                    format_currency(new_total)
                ))
                
                select_window.destroy()
                sales_window.deiconify()
                messagebox.showinfo("Thành công", f"Đã tăng số lượng {product_name} lên {new_qty} trong đơn hàng.")
                return


        # Nếu sản phẩm chưa có trong đơn hàng thì thêm mới
        detail_tree.insert("", END, values=(
            product_name, 
            format_currency(original_price), 
            quantity, 
            format_currency(total_price)
        ))
        
        select_window.destroy()
        sales_window.deiconify()
        
        messagebox.showinfo("Thành công", f"Đã thêm {product_name} vào đơn hàng.")

    Button(select_window, 
           text="Thêm sản phẩm đã chọn vào Đơn hàng (SL: 1)", 
           width=40,
           height=2,
           bg="#4CAF50", 
           fg='white',
           font=("Arial", 10, 'bold'),
           command=add_selected_product_to_order).pack(pady=10)

    def go_back_to_brand_selection():
        select_window.destroy()
        parent_menu_window.deiconify()
        
    Button(select_window, 
           text="< Trở lại Menu Hãng", 
           width=30, 
           height=1, 
           bg="#B0BEC5", 
           fg='black',
           font=("Arial", 10, 'bold'),
           command=go_back_to_brand_selection).pack(pady=20)


# ===== HÀM XỬ LÝ GIAO DỊCH VÀ TRỪ KHO  =====

def finalize_sales_transaction(product_details):
    """
    Thực hiện trừ số lượng sản phẩm đã bán khỏi bảng kho (xóa bản ghi MaSP).
    product_details là list các tuple: (Tên SP, Đơn giá, Số lượng, Thành tiền)
    """
    conn = connect_db()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        
        for item in product_details:
            product_name = item[0]
            # item[2] là số lượng bán ra (string từ Treeview)
            quantity_sold = int(item[2]) 

            # 1. Tìm kiếm MaSP của các sản phẩm cần xóa (MaSP là duy nhất cho mỗi đơn vị)
            # Lấy theo thứ tự NgayNhap sớm nhất (FIFO)
            query_select = """
                SELECT MaSP 
                FROM kho 
                WHERE TenSP = %s 
                ORDER BY NgayNhap ASC 
                LIMIT %s
            """
            cur.execute(query_select, (product_name, quantity_sold))
            
            masp_to_delete = [row[0] for row in cur.fetchall()]
            
            if len(masp_to_delete) < quantity_sold:
                # Trường hợp không đủ số lượng trong kho
                messagebox.showwarning("Lỗi Trừ Kho", f"Không đủ số lượng Mã sản phẩm ({product_name}) để trừ kho. Còn thiếu {quantity_sold - len(masp_to_delete)} sản phẩm.")
                conn.rollback()
                return False

            # 2. Xóa các bản ghi MaSP đã chọn
            for masp in masp_to_delete:
                query_delete = "DELETE FROM kho WHERE MaSP = %s"
                cur.execute(query_delete, (masp,))
            
        conn.commit()
        return True

    except mysql.connector.Error as e:
        conn.rollback()
        messagebox.showerror("Lỗi CSDL Trừ Kho", f"Lỗi trong quá trình trừ kho: {e}")
        return False
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Lỗi Hệ thống", f"Lỗi không xác định khi trừ kho: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

# ===== LƯU LỊCH SỬ BÁN HÀNG VÀO CSDL =====
def save_sales_history(sales_data, product_details, total_payment):
    """
    Lưu thông tin hóa đơn vào các bảng hoadon và chitiet_hoadon.
    """
    conn = connect_db()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # 1. Lưu vào bảng hoadon
        query_hoadon = """
            INSERT INTO hoadon (MaDon, NgayTaoDon, TenKH, SDT, DiaChiGH, PhuongThucTT, PhuongThucNH, TongThanhToan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query_hoadon, (
            sales_data['ma_don'],
            sales_data['ngay_tao_don'],
            sales_data['ten_kh'],
            sales_data['sdt'],
            sales_data['dia_chi_gh'],
            sales_data['phuong_thuc_tt'],
            sales_data['phuong_thuc_nh'],
            total_payment
        ))
        
        # 2. Lưu vào bảng chitiet_hoadon
        query_chitiet = """
            INSERT INTO chitiet_hoadon (MaDon, TenSP, DonGia, SoLuong, ThanhTien)
            VALUES (%s, %s, %s, %s, %s)
        """
        for item in product_details:
            product_name = item[0]
            unit_price = unformat_currency(item[1])
            quantity = int(item[2])
            subtotal = unformat_currency(item[3])
            
            cur.execute(query_chitiet, (
                sales_data['ma_don'],
                product_name,
                unit_price,
                quantity,
                subtotal
            ))
            
        conn.commit()
        return True
        
    except mysql.connector.Error as e:
        conn.rollback()
        # Kiểm tra lỗi trùng khóa chính (MaDon)
        if e.errno == 1062: # 1062 is ER_DUP_ENTRY
             messagebox.showerror("Lỗi CSDL", f"Mã đơn hàng '{sales_data['ma_don']}' đã tồn tại.")
        else:
             messagebox.showerror("Lỗi CSDL Lưu Lịch Sử", f"Lỗi khi lưu lịch sử bán hàng: {e}")
        return False
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Lỗi Hệ thống", f"Lỗi không xác định khi lưu lịch sử: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

# ===== HÀM TẠO CỬA SỔ HÓA ĐƠN VÀ THANH TOÁN =====

def show_invoice(sales_data, product_details, sales_window_ref):
    """
    Hiển thị cửa sổ hóa đơn với chi tiết đơn hàng và tổng thanh toán.
    sales_window_ref: Tham chiếu cửa sổ bán hàng để đóng lại khi hoàn tất.
    """
    invoice_window = Toplevel(root)
    invoice_window.title("HÓA ĐƠN THANH TOÁN")
    center_window(invoice_window, 800, 800) # Căn giữa cửa sổ
    invoice_window.configure(bg='#e0f7fa')
    
    # Tính tổng thanh toán trước (giá trị số)
    total_payment = 0
    for product in product_details:
        total_payment += unformat_currency(product[3]) 

    # --- CHỨC NĂNG IN VÀ HOÀN THÀNH GIAO DỊCH ---
    def print_invoice_action():
        # Dùng thuộc tính của hàm để tránh trừ kho nhiều lần
        if not hasattr(print_invoice_action, 'transaction_completed'):
            print_invoice_action.transaction_completed = False

        if print_invoice_action.transaction_completed:
            messagebox.showinfo("Thông báo", "Giao dịch này đã được hoàn thành và trừ kho.")
            return

        if messagebox.askyesno("Xác nhận Thanh toán", "Bạn có chắc chắn muốn HOÀN TẤT giao dịch?"):
            # 1. TRỪ KHO
            if finalize_sales_transaction(product_details):
                # 2. LƯU LỊCH SỬ BÁN HÀNG VÀO CSDL
                if save_sales_history(sales_data, product_details, total_payment):
                    messagebox.showinfo("Thành công", "Giao dịch đã được ghi nhận. Hệ thống sẽ quay lại Menu Chính.")
                    print_invoice_action.transaction_completed = True
                    
                    # 3. Đóng các cửa sổ
                    invoice_window.destroy()
                    sales_window_ref.destroy() 
                    root.deiconify() 
                else:
                    # Lỗi đã được hiển thị bên trong save_sales_history
                    messagebox.showwarning("Thất bại", "Lưu lịch sử bán hàng thất bại. Đã trừ kho nhưng chưa lưu hóa đơn.")
            else:
                # Lỗi đã được hiển thị bên trong finalize_sales_transaction
                messagebox.showwarning("Thất bại", "Trừ kho thất bại. Vui lòng kiểm tra lại CSDL và số lượng tồn kho.")
    
    def go_back():
        invoice_window.destroy()

    Label(invoice_window, text="HÓA ĐƠN BÁN HÀNG", 
          font=("Arial", 24, "bold"), 
          fg='#004d40', 
          bg='#e0f7fa').pack(pady=20)
    
    # --- Khung Thông tin Khách hàng và Đơn hàng ---
    info_frame = Frame(invoice_window, bg='#f3fdee', padx=20, pady=10, bd=1, relief=SUNKEN)
    info_frame.pack(fill='x', padx=30, pady=(0, 15))
    
    Label(info_frame, text="Mã đơn hàng:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=2)
    Label(info_frame, text=sales_data['ma_don'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=0, column=1, sticky='w', padx=5, pady=2)
    
    Label(info_frame, text="Ngày tạo đơn:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=1, column=0, sticky='w', padx=5, pady=2)
    Label(info_frame, text=sales_data['ngay_tao_don'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=1, column=1, sticky='w', padx=5, pady=2)
    
    Label(info_frame, text="P.thức TT:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=2, column=0, sticky='w', padx=5, pady=2)
    Label(info_frame, text=sales_data['phuong_thuc_tt'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=2, column=1, sticky='w', padx=5, pady=2)
    
    Label(info_frame, text="P.thức NH:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=3, column=0, sticky='w', padx=5, pady=2)
    Label(info_frame, text=sales_data['phuong_thuc_nh'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=3, column=1, sticky='w', padx=5, pady=2)
    
    Label(info_frame, text="Khách hàng:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=0, column=2, sticky='w', padx=30, pady=2)
    Label(info_frame, text=sales_data['ten_kh'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=0, column=3, sticky='w', padx=5, pady=2)
    
    Label(info_frame, text="SĐT:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=1, column=2, sticky='w', padx=30, pady=2)
    Label(info_frame, text=sales_data['sdt'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=1, column=3, sticky='w', padx=5, pady=2)
    
    Label(info_frame, text="Địa chỉ GH:", bg='#f3fdee', anchor='w', font=("Arial", 10, 'bold')).grid(row=2, column=2, sticky='w', padx=30, pady=2)
    Label(info_frame, text=sales_data['dia_chi_gh'], bg='#f3fdee', anchor='w', font=("Arial", 10)).grid(row=2, column=3, sticky='w', padx=5, pady=2)

    # --- Khung Chi tiết Sản phẩm ---
    product_frame = Frame(invoice_window, padx=30, bg='#e0f7fa'); product_frame.pack(fill='both', expand=True)

    Label(product_frame, text="CHI TIẾT MUA HÀNG", 
          font=("Arial", 16, "bold"), 
          fg='#004d40', 
          bg='#e0f7fa').pack(pady=(10, 5))
    
    list_frame_detail = Frame(product_frame, padx=10, bg='#fff'); list_frame_detail.pack(pady=10, fill='both', expand=True)

    columns_detail = ("Tên sản phẩm", "Đơn giá (VND)", "Số lượng", "Thành tiền (VND)")
    tree_detail = ttk.Treeview(list_frame_detail, columns=columns_detail, show='headings', height=15)

    for col in columns_detail: tree_detail.heading(col, text=col, anchor=CENTER)

    tree_detail.column("Tên sản phẩm", width=250, anchor=W); tree_detail.column("Đơn giá (VND)", width=120, anchor=E)
    tree_detail.column("Số lượng", width=80, anchor=CENTER); tree_detail.column("Thành tiền (VND)", width=120, anchor=E)

    scrollbar_detail = ttk.Scrollbar(list_frame_detail, orient="vertical", command=tree_detail.yview)
    tree_detail.configure(yscrollcommand=scrollbar_detail.set); scrollbar_detail.pack(side="right", fill="y"); tree_detail.pack(side="left", fill='both', expand=True)
    
    # Điền dữ liệu chi tiết sản phẩm 
    for product in product_details:
        tree_detail.insert("", END, values=product)

    # --- Khung Tổng thanh toán ---
    total_frame = Frame(invoice_window, bg='#004d40', padx=30, pady=10, bd=1, relief=SUNKEN)
    total_frame.pack(fill='x', padx=30, pady=(15, 20))
    
    Label(total_frame, text="TỔNG THANH TOÁN (VND):", 
          font=("Arial", 16, "bold"), 
          fg='white', 
          bg='#004d40').pack(side=LEFT, padx=10)
          
    Label(total_frame, text=format_currency(total_payment), 
          font=("Arial", 16, "bold"), 
          fg='#ffeb3b', # Màu vàng nổi bật
          bg='#004d40').pack(side=RIGHT, padx=10)


    # --- Nút chức năng ---
    button_frame = Frame(invoice_window, bg='#e0f7fa'); button_frame.pack(pady=10)

    Button(button_frame, 
           text="In hoá đơn", 
           width=35, 
           height=2, 
           bg="#03A9F4", 
           fg='white', 
           font=("Arial", 12, 'bold'),
           command=print_invoice_action).pack(side=LEFT, padx=10)
           
    Button(button_frame, 
           text="Quay lại", 
           width=20, 
           height=2, 
           bg="#607D8B", 
           fg='white', 
           font=("Arial", 12, 'bold'),
           command=go_back).pack(side=LEFT, padx=10)


# ===== HÀM TẠO CỬA SỔ GIAO DIỆN BÁN HÀNG =====
def open_sales_interface_window():
    """Mở cửa sổ giao diện bán hàng."""
    sales_window = Toplevel(root)
    sales_window.title("Giao diện Bán hàng")
    center_window(sales_window, 1000, 750) # Căn giữa cửa sổ
    sales_window.configure(bg='#e8f5e9')

    def go_back_to_main():
        sales_window.destroy()
        root.deiconify() 

    def start_selection_flow(sales_window, detail_tree):
        sales_window.withdraw()
        open_selection_menu(sales_window, tree_detail) 
        
    def delete_selected_product():
        selected_item = tree_detail.focus()
        if not selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một sản phẩm trong đơn hàng để xóa.")
            return
        
        product_name = tree_detail.item(selected_item, 'values')[0]
        
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa sản phẩm:\n{product_name} khỏi đơn hàng không?"):
            tree_detail.delete(selected_item)
            messagebox.showinfo("Thành công", f"Đã xóa sản phẩm {product_name} khỏi đơn hàng.")
    
    # --- HÀM XỬ LÝ THANH TOÁN --
    def process_payment():
        ma_don = var_ma_don.get().strip()
        ten_kh = var_ten_kh.get().strip()
        sdt = var_sdt.get().strip()
        dia_chi_gh = var_dia_chi_gh.get().strip()
        pt_nh = var_phuong_thuc_nh.get().strip()
        
        # 1. Kiểm tra thông tin bắt buộc
        if not ma_don:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập **Mã đơn hàng**.")
            return
        if not ten_kh:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập **Tên khách hàng**.")
            return
        if not sdt:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập **SĐT Khách hàng**.")
            return
        
        # 2. Kiểm tra địa chỉ giao hàng nếu chọn Giao hàng tận nơi
        if pt_nh == "Giao hàng tận nơi" and not dia_chi_gh:
            messagebox.showwarning("Thiếu thông tin", "Bạn đã chọn **Giao hàng tận nơi**, vui lòng nhập **Địa chỉ giao hàng**.")
            return
            
        product_details = []
        for item in tree_detail.get_children():
            product_details.append(tree_detail.item(item, 'values'))
            
        if not product_details:
            messagebox.showwarning("Thiếu sản phẩm", "Vui lòng chọn ít nhất một sản phẩm.")
            return

        sales_data = {
            'ma_don': ma_don,
            'ngay_tao_don': var_ngay_tao_don.get().strip(),
            'phuong_thuc_tt': var_phuong_thuc_tt.get().strip(),
            'phuong_thuc_nh': pt_nh,
            'ten_kh': ten_kh,
            'sdt': sdt,
            'dia_chi_gh': dia_chi_gh,
        }
        
        # Kiểm tra xem mã đơn hàng đã tồn tại trong CSDL lịch sử chưa (tránh trùng lặp khi quay lại)
        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT MaDon FROM hoadon WHERE MaDon = %s", (ma_don,))
                if cur.fetchone():
                    messagebox.showwarning("Lỗi trùng mã", f"Mã đơn hàng '{ma_don}' đã tồn tại trong lịch sử bán hàng. Vui lòng sử dụng mã khác.")
                    return
            except Exception as e:
                # Bỏ qua lỗi nếu bảng hoadon chưa tồn tại
                pass
            finally:
                if conn and conn.is_connected():
                    conn.close()


        show_invoice(sales_data, product_details, sales_window)
    Label(sales_window, text="GIAO DIỆN BÁN HÀNG", font=("Arial", 24, "bold"), fg='#2e7d32', bg='#e8f5e9').pack(pady=20)
    
    # --- Khung Thông tin Đơn hàng ---
    info_frame = Frame(sales_window, bg='#f3fdee', padx=20, pady=10, bd=2, relief=GROOVE)
    info_frame.pack(fill='x', padx=30, pady=10)
    
    var_ma_don = StringVar()
    var_ngay_tao_don = StringVar(value=datetime.date.today().strftime("%Y-%m-%d")) 
    var_phuong_thuc_tt = StringVar(value="Tiền mặt")
    var_phuong_thuc_nh = StringVar(value="Giao hàng tận nơi")
    var_ten_kh = StringVar()
    var_sdt = StringVar()
    var_dia_chi_gh = StringVar()

    col1_frame = Frame(info_frame, bg='#f3fdee'); col1_frame.pack(side=LEFT, padx=5, pady=5, expand=True, fill='both')
    col2_frame = Frame(info_frame, bg='#f3fdee'); col2_frame.pack(side=LEFT, padx=5, pady=5, expand=True, fill='both')

    payment_options = ["Tiền mặt", "Chuyển khoản"]
    delivery_options = ["Giao hàng tận nơi", "Nhận tại cửa hàng"]

    base_label_args = {"width": 15, "anchor": 'w', "bg": '#f3fdee'}
    font_regular = ("Arial", 10);
    font_bold = ("Arial", 10, 'bold')
    
    Frame_MaDon = Frame(col1_frame, bg='#f3fdee'); Frame_MaDon.pack(fill='x', pady=5)
    Label(Frame_MaDon, text="Mã đơn hàng", **base_label_args, font=font_bold).pack(side=LEFT, padx=5)
    Entry(Frame_MaDon, width=25, bd=2, relief=SUNKEN, textvariable=var_ma_don).pack(side=RIGHT, padx=5, expand=True, fill='x')

    Frame_NgayTao = Frame(col1_frame, bg='#f3fdee'); Frame_NgayTao.pack(fill='x', pady=5)
    Label(Frame_NgayTao, text="Ngày tạo đơn", **base_label_args, font=font_regular).pack(side=LEFT, padx=5)
    Entry(Frame_NgayTao, width=25, bd=2, relief=SUNKEN, textvariable=var_ngay_tao_don).pack(side=RIGHT, padx=5, expand=True, fill='x')

    Frame_Pttt = Frame(col1_frame, bg='#f3fdee'); Frame_Pttt.pack(fill='x', pady=5)
    Label(Frame_Pttt, text="P.thức Thanh toán", **base_label_args, font=font_regular).pack(side=LEFT, padx=5)
    ttk.Combobox(Frame_Pttt, textvariable=var_phuong_thuc_tt, values=payment_options, state="readonly", width=22).pack(side=RIGHT, padx=5, expand=True, fill='x')

    Frame_Ptnh = Frame(col1_frame, bg='#f3fdee'); Frame_Ptnh.pack(fill='x', pady=5)
    Label(Frame_Ptnh, text="P.thức Nhận hàng", **base_label_args, font=font_regular).pack(side=LEFT, padx=5)
    cbb_ptnh = ttk.Combobox(Frame_Ptnh, textvariable=var_phuong_thuc_nh, values=delivery_options, state="readonly", width=22)
    cbb_ptnh.pack(side=RIGHT, padx=5, expand=True, fill='x')

    Frame_TenKH = Frame(col2_frame, bg='#f3fdee'); Frame_TenKH.pack(fill='x', pady=5)
    Label(Frame_TenKH, text="Tên khách hàng", **base_label_args, font=font_bold).pack(side=LEFT, padx=5)
    Entry(Frame_TenKH, width=25, bd=2, relief=SUNKEN, textvariable=var_ten_kh).pack(side=RIGHT, padx=5, expand=True, fill='x')

    Frame_SDT = Frame(col2_frame, bg='#f3fdee'); Frame_SDT.pack(fill='x', pady=5)
    Label(Frame_SDT, text="SĐT Khách hàng", **base_label_args, font=font_bold).pack(side=LEFT, padx=5)
    Entry(Frame_SDT, width=25, bd=2, relief=SUNKEN, textvariable=var_sdt).pack(side=RIGHT, padx=5, expand=True, fill='x')

    Frame_DiaChi = Frame(col2_frame, bg='#f3fdee'); Frame_DiaChi.pack(fill='x', pady=5)
    Label(Frame_DiaChi, text="Địa chỉ giao hàng", **base_label_args, font=font_bold).pack(side=LEFT, padx=5)
    entry_diachi = Entry(Frame_DiaChi, width=25, bd=2, relief=SUNKEN, textvariable=var_dia_chi_gh)
    entry_diachi.pack(side=RIGHT, padx=5, expand=True, fill='x')
    
    # --- Khung Chi tiết Sản phẩm ---
    product_detail_frame = Frame(sales_window, bg='#fff', padx=20, pady=10, bd=2, relief=GROOVE); 
    product_detail_frame.pack(fill='both', padx=30, pady=10, expand=True)
    Label(product_detail_frame, text="CHI TIẾT SẢN PHẨM TRONG ĐƠN", font=("Arial", 14, "bold"), fg='#2e7d32', bg='#fff').pack(pady=(5, 10))

    list_frame_detail = Frame(product_detail_frame, padx=10, bg='#fff'); list_frame_detail.pack(pady=10, fill='both', expand=True)

    columns_detail = ("Tên sản phẩm", "Đơn giá (VND)", "Số lượng", "Thành tiền (VND)")
    tree_detail = ttk.Treeview(list_frame_detail, columns=columns_detail, show='headings', height=10)

    for col in columns_detail: tree_detail.heading(col, text=col, anchor=CENTER)

    tree_detail.column("Tên sản phẩm", width=300, anchor=W); tree_detail.column("Đơn giá (VND)", width=150, anchor=E)
    tree_detail.column("Số lượng", width=80, anchor=CENTER); tree_detail.column("Thành tiền (VND)", width=150, anchor=E)

    scrollbar_detail = ttk.Scrollbar(list_frame_detail, orient="vertical", command=tree_detail.yview)
    tree_detail.configure(yscrollcommand=scrollbar_detail.set); scrollbar_detail.pack(side="right", fill="y"); tree_detail.pack(side="left", fill='both', expand=True)
    
        
    # --- KHUNG NÚT CHỨC NĂNG CHÍNH (CẬP NHẬT BỐ CỤC) ---
    main_buttons_frame = Frame(sales_window, bg='#e8f5e9')
    main_buttons_frame.pack(pady=10)
    
    # Nút "Chọn sản phẩm (+)"
    Button(main_buttons_frame, 
           text="Chọn sản phẩm (+)", 
           width=20,
           height=2,
           bg='#FFC107', 
           fg='black', 
           font=("Arial", 10, 'bold'), 
           command=lambda: start_selection_flow(sales_window, tree_detail)
          ).pack(side=LEFT, padx=10)
    
    # Nút "Xóa sản phẩm đã chọn"
    Button(main_buttons_frame, 
           text="Xóa sản phẩm đã chọn (-)", 
           width=20,
           height=2,
           bg='#F44336', 
           fg='white', 
           font=("Arial", 10, 'bold'),
           command=delete_selected_product
          ).pack(side=LEFT, padx=10)

    # Nút "Thanh toán"
    Button(main_buttons_frame,
           text="Thanh toán",
           width=20,
           height=2,
           bg="#2196F3",
           fg='white',
           font=("Arial", 12, 'bold'),
           command=process_payment).pack(side=LEFT, padx=10)

    # Nút "Trở lại Menu Chính"
    Button(sales_window,
           text="< Trở lại Menu Chính",
           width=25,
           height=1,
           bg="#9E9E9E",
           fg='white',
           font=("Arial", 10, 'bold'),
           command=go_back_to_main).pack(pady=10)


# ===== HÀM TẠO CỬA SỔ LỊCH SỬ BÁN HÀNG  =====
def open_sales_history_window(): 
    history_window = Toplevel(root)
    history_window.title("Lịch sử bán hàng")
    center_window(history_window, 1200, 600)
    history_window.configure(bg='#f5f5f5')
    
    # --- HÀM XUẤT EXCEL ---
    def export_excel():
        conn = connect_db()
        if not conn: return
        try:
            cur = conn.cursor()
            # Lấy dữ liệu chi tiết để xuất Excel
            query = """
                SELECT 
                    hd.MaDon, hd.NgayTaoDon, hd.TenKH, 
                    ct.TenSP, ct.SoLuong, ct.DonGia, ct.ThanhTien
                FROM hoadon hd
                JOIN chitiet_hoadon ct ON hd.MaDon = ct.MaDon
                ORDER BY hd.NgayTaoDon DESC, hd.MaDon DESC
            """
            cur.execute(query)
            rows = cur.fetchall()
            columns = ["Mã Đơn", "Ngày Tạo", "Khách Hàng", "Tên Sản Phẩm", "Số Lượng", "Đơn Giá", "Thành Tiền"]
            
            # Tạo DataFrame và xuất file
            df = pd.DataFrame(rows, columns=columns)
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                   filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                                                   title="Lưu file Excel Lịch sử Bán hàng")
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Thành công", f"Đã xuất file Excel thành công tại:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Lỗi Xuất Excel", f"Lỗi: {e}")
        finally:
            if conn and conn.is_connected(): conn.close()

    Label(history_window, text="LỊCH SỬ BÁN HÀNG", font=("Arial", 20, "bold"), fg='#E64A19', bg='#f5f5f5').pack(pady=20)
    
    h_frame = Frame(history_window, padx=20, bg='#f5f5f5'); h_frame.pack(pady=10, fill='both', expand=True)
    tree = ttk.Treeview(h_frame, columns=("Mã", "Ngày", "KH", "SP", "SL", "Tiền"), show='headings')
    for c in ("Mã", "Ngày", "KH", "SP", "SL", "Tiền"): tree.heading(c, text=c)
    tree.pack(side='left', fill='both', expand=True)
    
    def load_history():
        conn = connect_db()
        if not conn: return
        try:
            for i in tree.get_children(): tree.delete(i)
            cur = conn.cursor()
            query = """SELECT hd.MaDon, hd.NgayTaoDon, hd.TenKH, ct.TenSP, ct.SoLuong, hd.TongThanhToan
                FROM hoadon hd JOIN chitiet_hoadon ct ON hd.MaDon = ct.MaDon ORDER BY hd.NgayTaoDon DESC"""
            cur.execute(query)
            last_ma = None
            for row in cur.fetchall():
                r = list(row); ma = r[0]
                if ma == last_ma: r[0]=""; r[1]=""; r[2]=""; r[5]="" # Gom nhóm hiển thị đẹp
                else: r[5] = format_currency(r[5])
                tree.insert("", END, values=r); last_ma = ma
        except Exception as e: messagebox.showerror("Lỗi", str(e))
        finally: 
            if conn and conn.is_connected(): conn.close()
    load_history()
    
    btn_frame = Frame(history_window, bg='#f5f5f5'); btn_frame.pack(pady=20)
    
    # Nút Xuất Excel
    Button(btn_frame, text="Xuất ra Excel (.xlsx)", width=20, height=2, bg="#4CAF50", fg='white', font=("Arial", 10, "bold"), 
           command=export_excel).pack(side=LEFT, padx=10)
           
    Button(btn_frame, text="Quay lại", width=20, height=2, bg="#795548", fg='white', font=("Arial", 10, "bold"), 
           command=lambda: [history_window.destroy(), root.deiconify()]).pack(side=LEFT, padx=10)
# --- Khởi tạo cửa sổ chính ---
root = Tk()
root.title("Quản Lý Cửa Hàng")
root.geometry("500x500") # Đặt kích thước cố định
center_window(root, 500, 500) # Căn giữa cửa sổ chính

# --- Tạo thanh Menu ---
menubar = Menu(root)
root.config(menu=menubar)

# Tạo menu con "Chức năng"
chuc_nang_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="MENU", menu=chuc_nang_menu)

# Thêm các mục vào menu "Chức năng"
# 1. Bán hàng
chuc_nang_menu.add_command(label="Giao diện Bán hàng", 
                           command=lambda: [root.withdraw(), open_sales_interface_window()])

# 2. Kho
chuc_nang_menu.add_command(label="Kho", 
                           command=lambda: [root.withdraw(), open_employee_management_window()])

# 3. Lịch sử
chuc_nang_menu.add_command(label="Lịch sử bán hàng", 
                           command=lambda: [root.withdraw(), open_sales_history_window()])

chuc_nang_menu.add_separator()

# 4. Thoát
chuc_nang_menu.add_command(label="Thoát chương trình", command=root.destroy)

Label(root, text="QUẢN LÝ CỬA HÀNG\nTHIẾT BỊ ĐIỆN TỬ", 
      fg="#1565C0", 
      font=("Arial", 20, "bold")).pack(expand=True)

root.mainloop()

