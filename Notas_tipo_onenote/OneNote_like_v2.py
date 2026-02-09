import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import datetime
from openpyxl import Workbook

DB_FILE = "notas_movil.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            state TEXT,
            tags TEXT,
            archived INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()

    # Insertar estados por defecto si no existen
    default_states = ["Por hacer", "En Progreso", "Completado", "Pendiente"]
    for st in default_states:
        try:
            c.execute('INSERT INTO states(name) VALUES(?)', (st,))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def fetchall(query, params=()): 
    with sqlite3.connect(DB_FILE) as conn:
        return list(conn.execute(query, params))

def execute(query, params=()): 
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de notas")
        self.root.geometry("1100x600")

        self.selected_note = None
        self.show_archived = False

        self.setup_ui()
        self.load_states()
        self.load_tags()
        self.load_notes()

    def setup_ui(self):
        izquierda = tk.Frame(self.root, width=250)
        izquierda.pack(side=tk.LEFT, fill=tk.Y)
        self.tree = ttk.Treeview(izquierda, columns=["Estado"], show='headings')
        self.tree.heading("Estado", text="Estado")
        self.tree.pack(fill=tk.Y, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_note_select)

        btn_frame = tk.Frame(izquierda)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Nueva nota", command=self.new_note).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Editar", command=self.edit_note).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_note).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Archivar", command=self.archive_note).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Mostrar Archivadas", command=self.toggle_archived).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Editar estados", command=self.manage_states).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Exportar a Excel", command=self.export_excel).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Buscar", command=self.search_notes).pack(fill=tk.X)

        derecho = tk.Frame(self.root)
        derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        top_right = tk.Frame(derecho)
        top_right.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(top_right, text="Título:").pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        ttk.Entry(top_right, textvariable=self.title_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        ttk.Label(top_right, text="Estado:").pack(side=tk.LEFT, padx=2)
        self.state_var = tk.StringVar()
        self.state_menu = ttk.OptionMenu(top_right, self.state_var, '')
        self.state_menu.pack(side=tk.LEFT)

        ttk.Label(top_right, text="Etiquetas (separadas por coma):").pack(side=tk.LEFT, padx=2)
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk.Entry(top_right, textvariable=self.tags_var, width=30)
        self.tags_entry.pack(side=tk.LEFT)

        self.text_content = tk.Text(derecho, wrap=tk.WORD, font=("Arial", 12))
        self.text_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        inferior = tk.Frame(derecho)
        inferior.pack(fill=tk.X)
        ttk.Button(inferior, text="Adjuntar archivo", command=self.attach_file).pack(side=tk.LEFT)
        ttk.Button(inferior, text="Guardar nota", command=self.save_note).pack(side=tk.LEFT)
        ttk.Button(inferior, text="Insertar lista", command=self.insert_list).pack(side=tk.LEFT)
        ttk.Button(inferior, text="Insertar negrita", command=lambda: self.insert_markdown("**", "**")).pack(side=tk.LEFT)
        ttk.Button(inferior, text="Insertar cursiva", command=lambda: self.insert_markdown("_", "_")).pack(side=tk.LEFT)

    def load_states(self):
        states = fetchall("SELECT name FROM states ORDER BY name")
        menu = self.state_menu["menu"]
        menu.delete(0, "end")
        for state in states:
            menu.add_command(label=state[0], command=lambda value=state[0]: self.state_var.set(value))
        if states:
            self.state_var.set(states[0][0])

    def load_tags(self):
        self.all_tags = [tag[0] for tag in fetchall("SELECT name FROM tags ORDER BY name")]

    def load_notes(self):
        self.tree.delete(*self.tree.get_children())
        archived_filter = 1 if self.show_archived else 0
        notes = fetchall('SELECT id, title, state FROM notes WHERE archived=?', (archived_filter,))
        for note in notes:
            note_id, title, state = note
            self.tree.insert('', 'end', iid=note_id, values=(title, state))
        self.clear_selected()

    def clear_selected(self):
        self.selected_note = None
        self.title_var.set("")
        self.tags_var.set("")
        self.state_var.set('')
        self.text_content.delete('1.0', tk.END)

    def on_note_select(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return
        note = fetchall('SELECT * FROM notes WHERE id=?', (item_id,))
        if note:
            self.selected_note = item_id
            _, title, content, state, tags, archived, created_at, updated_at = note[0]
            self.title_var.set(title)
            self.tags_var.set(tags)
            self.state_var.set(state)
            self.text_content.delete('1.0', tk.END)
            self.text_content.insert(tk.END, content)

    def new_note(self):
        self.clear_selected()
        self.selected_note = None

    def edit_note(self):
        if self.selected_note:
            self.on_note_select(None)
        else:
            messagebox.showinfo("Editar", "Selecciona una nota para editar.")

    def save_note(self):
        title = self.title_var.get()
        content = self.text_content.get('1.0', tk.END)
        state = self.state_var.get()
        tags = self.tags_var.get()
        now = datetime.datetime.now().isoformat()
        if self.selected_note:
            execute('''UPDATE notes SET title=?, content=?, state=?, tags=?, updated_at=? WHERE id=?''',
                    (title, content, state, tags, now, self.selected_note))
        else:
            execute('''INSERT INTO notes (title, content, state, tags, archived, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, ?, ?)''',
                    (title, content, state, tags, now, now))
        self.load_notes()

    def delete_note(self):
        if self.selected_note:
            execute('DELETE FROM notes WHERE id=?', (self.selected_note,))
            self.load_notes()
        else:
            messagebox.showinfo("Eliminar", "Selecciona una nota para eliminar.")

    def archive_note(self):
        if not self.selected_note:
            messagebox.showinfo("Archivar", "Selecciona una nota para archivar.")
            return
        execute('UPDATE notes SET archived=1 WHERE id=?', (self.selected_note,))
        self.load_notes()
        self.clear_selected()

    def toggle_archived(self):
        self.show_archived = not self.show_archived
        self.load_notes()
        state_msg = "Notas archivadas" if self.show_archived else "Notas activas"
        messagebox.showinfo("Vista notas", f"Ahora mostrando {state_msg}.")

    def search_notes(self):
        term = simpledialog.askstring("Buscar", "Ingresa texto, etiqueta o estado:")
        if not term:
            return
        self.tree.delete(*self.tree.get_children())
        archived_filter = 1 if self.show_archived else 0
        query = '''
            SELECT id, title, state FROM notes 
            WHERE archived=? AND 
            (title LIKE ? OR content LIKE ? OR tags LIKE ? OR state LIKE ?)'''
        param = f'%{term}%'
        results = fetchall(query, (archived_filter, param, param, param, param))
        for r in results:
            self.tree.insert('', 'end', iid=r[0], values=(r[1], r[2]))

    def attach_file(self):
        if not self.selected_note:
            messagebox.showwarning("Aviso", "Primero selecciona o crea una nota.")
            return
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        filename = os.path.basename(filepath)
        target_dir = os.path.join(os.getcwd(), 'attachments')
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)
        try:
            with open(filepath, 'rb') as fsrc, open(target_path, 'wb') as fdst:
                fdst.write(fsrc.read())
        except Exception as e:
            messagebox.showerror("Error", f"Error al copiar archivo: {e}")
            return
        messagebox.showinfo("Archivo adjuntado", "Archivo guardado correctamente.")

    def insert_list(self):
        self.text_content.insert(tk.INSERT, "- ")

    def insert_markdown(self, left, right):
        try:
            start = self.text_content.index("sel.first")
            end = self.text_content.index("sel.last")
            selected_text = self.text_content.get(start, end)
            self.text_content.delete(start, end)
            self.text_content.insert(start, f"{left}{selected_text}{right}")
        except tk.TclError:
            self.text_content.insert(tk.INSERT, f"{left}{right}")

    def export_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Título", "Contenidos", "Estado", "Etiquetas", "Archivado", "Creado", "Actualizado"])
        all_notes = fetchall('SELECT * FROM notes')
        for n in all_notes:
            ws.append(n)
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if filename:
            wb.save(filename)
            messagebox.showinfo("Exportar", "Datos exportados a Excel correctamente.")

    def manage_states(self):
        win = tk.Toplevel(self.root)
        win.title("Gestionar Estados")
        win.geometry("300x400")
        listbox = tk.Listbox(win)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        estados = fetchall("SELECT name FROM states ORDER BY name")
        for e in estados:
            listbox.insert(tk.END, e[0])
        frame = tk.Frame(win)
        frame.pack(fill=tk.X, padx=10, pady=5)
        new_state_var = tk.StringVar()
        tk.Entry(frame, textvariable=new_state_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        def add_state():
            nombre = new_state_var.get().strip()
            if not nombre:
                return
            try:
                execute("INSERT INTO states(name) VALUES(?)", (nombre,))
                listbox.insert(tk.END, nombre)
                new_state_var.set("")
                self.load_states()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Estado ya existe.")
        tk.Button(frame, text="Añadir", command=add_state).pack(side=tk.LEFT, padx=5)

        def delete_state():
            sel = listbox.curselection()
            if not sel:
                return
            estado = listbox.get(sel[0])
            if messagebox.askyesno("Confirmar", f"Eliminar estado '{estado}'?"):
                execute("DELETE FROM states WHERE name=?", (estado,))
                listbox.delete(sel[0])
                self.load_states()
        tk.Button(win, text="Eliminar Estado Seleccionado", command=delete_state).pack(pady=5)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
