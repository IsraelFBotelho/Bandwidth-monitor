import psutil
import time
import threading
import dearpygui.dearpygui as dpg
import numpy as np
from dearpygui_ext.themes import create_theme_imgui_light

UPDATE_DELAY = 1 # in seconds
RUNNING = True


dpg.create_context()
light_theme = create_theme_imgui_light()
dpg.bind_theme(light_theme)


def get_size(bytes):
    bytes /= (1024)*(1024)
    bytes *= 8
    return bytes


def bandwidth_line(time_l, download, new_download):
    if len(download) > (20+2/UPDATE_DELAY):
        download.pop(1)
    download.pop(-1)
    download.append(new_download)
    download.append(0)

def detect_attack(mean_l:list, new_download):

    std = np.std(mean_l)
    lim_s = np.mean(mean_l) + 3*std
    lim_i = np.mean(mean_l) - 3*std

    if new_download > lim_s:
        return True
    if new_download < lim_i:
        return False

    # mean_l.append(new_download)
    return False


io = psutil.net_io_counters()
bytes_sent, bytes_recv = io.bytes_sent, io.bytes_recv


time_l = []
download = []
mean_l = []
mean_l.append(20)
mean_l.append(22)
mean_l.append(36)
mean_l.append(52)
color = [255, 255, 0, 100]
attack = 0
attack_aux = False
attack_start = 21
for i in np.arange(0,20+3, UPDATE_DELAY):
    time_l.append(i)
    download.append(0)

def update():
    global attack, attack_aux, attack_start
    while RUNNING:
        global bytes_sent, bytes_recv, download, time_l
        time.sleep(UPDATE_DELAY)

        io_2 = psutil.net_io_counters()
        us, ds = io_2.bytes_sent - bytes_sent, io_2.bytes_recv - bytes_recv
        bytes_sent, bytes_recv = io_2.bytes_sent, io_2.bytes_recv

        if detect_attack(mean_l, get_size(ds / UPDATE_DELAY)):
            if not RUNNING:
                return
            attack = 3
            if not attack_aux:
                attack_aux = True
                dpg.delete_item("Bandwidth")
                dpg.add_area_series(time_l, download, label="Bandwidth", parent="y_axis", tag="Bandwidth", fill=[255, 0, 0, 100])
            if dpg.does_item_exist("dos"):
                dpg.delete_item("dos")
            dpg.add_plot_annotation(label="Um ataque foi detectado!", parent="plot", default_value=(attack_start, 50), offset=(-15,-15), color=[255, 100, 50, 255], tag="dos")
            if attack_start > 2:
                attack_start -=1
        elif attack == 0 and attack_aux:
            attack_aux = False
            dpg.delete_item("Bandwidth")
            dpg.add_area_series(time_l, download, label="Bandwidth", parent="y_axis", tag="Bandwidth", fill=[255, 255, 0, 100])
            if dpg.does_item_exist("dos"):
                dpg.delete_item("dos")
            attack_start = 21
        elif attack > 0:
            attack -= 1
            if dpg.does_item_exist("dos"):
                dpg.delete_item("dos")
            dpg.add_plot_annotation(label="Um ataque foi detectado!", parent="plot", default_value=(attack_start, 50), offset=(-15,-15), color=[255, 100, 50, 255], tag="dos")
            if attack_start > 2:
                attack_start -=1

            
        bandwidth_line(time_l, download, get_size(ds / UPDATE_DELAY))


def update_plot():
    dpg.set_value("Bandwidth", [time_l, download])

with dpg.window(label="Tutorial", tag="win"):

    with dpg.plot(label="Bandwidth Monitor", height=-1, width=-1, tag="plot"):
        dpg.add_plot_legend()

        dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Mbps", tag="y_axis")
        dpg.set_axis_limits("y_axis", 0, 100)
        dpg.set_axis_limits("x_axis", 0, 20)

        dpg.add_area_series(time_l, download, label="Bandwidth", parent="y_axis", tag="Bandwidth", fill=color)


dpg.create_viewport(title='Grafico de largura de rede', width=1000, height=1000)
dpg.setup_dearpygui()
dpg.show_viewport()

dpg.maximize_viewport()
dpg.set_primary_window("win", True)

thread = threading.Thread(target=update)
thread.start()

while dpg.is_dearpygui_running():
    update_plot()
    dpg.render_dearpygui_frame()

RUNNING = False
dpg.destroy_context()
