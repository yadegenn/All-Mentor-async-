import os
import sys
import tempfile
import subprocess
import shlex
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timezone, timedelta

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False

SEPARATOR = "␟"


def format_now_tz3():
    tz = timezone(timedelta(hours=3))
    now = datetime.now(tz)
    ts = now.strftime("%Y-%m-%d %H:%M:%S%z")
    return ts[:-2] + ":" + ts[-2:]


def convert_file(input_path, output_path):
    reg_date = format_now_tz3()
    bad_lines = []
    total = 0
    written = 0

    with open(input_path, "r", encoding="utf-8") as f_in, open(
        output_path, "w", encoding="utf-8"
    ) as f_out:
        for idx, line in enumerate(f_in, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                parts = shlex.split(line)
            except ValueError:
                bad_lines.append(idx)
                continue
            if len(parts) != 3:
                bad_lines.append(idx)
                continue
            chat_id, topic_id, user_name = parts
            nickname = user_name
            is_ban = "0"
            out_line = SEPARATOR.join(
                [chat_id, topic_id, nickname, user_name, is_ban, reg_date]
            )
            f_out.write(out_line + "\n")
            written += 1

    return total, written, bad_lines


def parse_dnd_path(data):
    data = data.strip()
    if data.startswith("{") and data.endswith("}"):
        return data[1:-1]
    return data


def on_drop_input(event):
    path = parse_dnd_path(event.data)
    if path:
        input_var.set(path)


def open_in_editor(path):
    if sys.platform.startswith("win"):
        subprocess.Popen(["notepad.exe", path])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def copy_file_as_object(path):
    uri = "file://" + os.path.abspath(path)
    gnome_payload = f"copy\n{uri}\n"
    if os.environ.get("WAYLAND_DISPLAY"):
        try:
            subprocess.run(
                ["wl-copy", "--type", "x-special/gnome-copied-files"],
                input=gnome_payload.encode("utf-8"),
                check=True,
            )
            return True, None
        except Exception:
            pass
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "x-special/gnome-copied-files"],
            input=gnome_payload.encode("utf-8"),
            check=True,
        )
        return True, None
    except Exception:
        pass

    try:
        subprocess.run(
            ["xsel", "--clipboard", "--mime-type", "x-special/gnome-copied-files", "--input"],
            input=gnome_payload.encode("utf-8"),
            check=True,
        )
        return True, None
    except Exception as exc:
        return False, exc


def run_convert():
    input_path = input_var.get().strip()

    if not input_path:
        messagebox.showerror("Ошибка", "Укажите входной файл.")
        return

    if not os.path.isfile(input_path):
        messagebox.showerror("Ошибка", "Входной файл не найден.")
        return

    output_fd, output_path = tempfile.mkstemp(suffix=".txt")
    os.close(output_fd)

    try:
        total, written, bad_lines = convert_file(input_path, output_path)
    except Exception as exc:
        messagebox.showerror("Ошибка", f"Не удалось конвертировать: {exc}")
        return

    msg = f"Готово. Обработано строк: {total}, записано: {written}."
    if bad_lines:
        msg += f"\nСтроки с ошибкой формата: {', '.join(map(str, bad_lines))}"
    ok, err = copy_file_as_object(output_path)
    if not ok:
        try:
            root.clipboard_clear()
            root.clipboard_append(output_path)
        except Exception as exc:
            msg += f"\nНе удалось скопировать путь в буфер: {exc}"
        if err:
            msg += f"\nНе удалось скопировать файл как объект: {err}"

    try:
        open_in_editor(output_path)
    except Exception as exc:
        msg += f"\nНе удалось открыть файл: {exc}"

    messagebox.showinfo("Успех", msg)

root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
root.title("TXT Конвертер")
root.geometry("640x200")
root.resizable(False, False)

input_var = tk.StringVar()

frame = tk.Frame(root, padx=12, pady=12)
frame.pack(fill=tk.BOTH, expand=True)

label_in = tk.Label(frame, text="Входной файл (chat_id topic_id user_name)")
label_in.pack(anchor="w")
row_in = tk.Frame(frame)
row_in.pack(fill=tk.X, pady=6)
entry_in = tk.Entry(row_in, textvariable=input_var)
entry_in.pack(side=tk.LEFT, fill=tk.X, expand=True)

btn_run = tk.Button(frame, text="Конвертировать", command=run_convert)
btn_run.pack(pady=12)

hint = tk.Label(
    frame,
    text=(
        "Разделитель: \"␟13␟\". nickname= username; is_ban=0; reg_date=сегодня. "
        "Вывод: файл в буфер и временный файл."
    ),
)
hint.pack(anchor="w")

if DND_AVAILABLE:
    entry_in.drop_target_register(DND_FILES)
    entry_in.dnd_bind("<<Drop>>", on_drop_input)
else:
    messagebox.showinfo(
        "Drag-and-drop",
        "Для drag-and-drop установите пакет: pip install tkinterdnd2",
    )

root.mainloop()
