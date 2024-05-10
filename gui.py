import asyncio
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

'''
- Install requirements.txt
- Update IP addresses below (GUI_IP, ROBOT_IP)
- Run Ameca_Live/osc_server.py in Tritium UI before starting gui
- To start GUI run: python3 gui.py
- To stop Gui: ctrl c
'''


# Update GUI_IP with the IP address of the machine that is running the GUI
GUI_IP = "192.168.101.111"
GUI_PORT = 54321

# Update ROBOT_IP with the robot IP address
ROBOT_IP = "192.168.101.103"
ROBOT_PORT = 12345


class OSCServer:
    def __init__(self):

        self.gui_ip = GUI_IP
        self.gui_port = GUI_PORT
        self.robot_ip = ROBOT_IP
        self.robot_port = ROBOT_PORT
    
        self.client = SimpleUDPClient(self.robot_ip, self.robot_port)
        self.targets = [] 
     

    def default_handler(self, addr, *args):
        print(f"OSC Message {addr!r}", repr(args))
        if addr == "/send_camera_targets":
            print("Recieved targets")
            self.targets = list(args)
            App.get_running_app().update_buttons(self.targets)

    
    # SEND TO TRITIUM OSC ############################################################
    
    # CHAT
    def send_start_chat_controller(self, test):
        self.client.send_message("/start_chat_controller", [])

    def send_stop_chat_controller(self, test):
        self.client.send_message("/stop_chat_controller", [])


    # MANUAL LISTEN
    def send_enable_listen(self, test):
        self.client.send_message("/enable_manual_listen_mode", [])

    def send_disable_listen(self, test):
        self.client.send_message("/disable_manual_listen_mode", [])

    def send_pause_asr(self, test):
        self.client.send_message("/pause_asr", [])
    
    def send_resume_asr(self, test):
        self.client.send_message("/resume_asr", [])

    def send_disable_listen(self, test):
        self.client.send_message("/disable_manual_listen_mode", [])

    def send_stop_listen(self, test):
        self.client.send_message("/stop_listening", [])

    def send_welcome_tts(self, test):
        self.client.send_message("/welcome_tts", [])


    # GAZE 
    def send_create_new_camera_target(self):
        self.client.send_message("/new_camera_target_mode", [])

    def send_get_saved_camera_targets(self):
        self.client.send_message("/get_camera_targets", [])

    def send_record_camera_target(self, name):
        self.client.send_message("/record_camera_target", [name])

    def send_look_at_camera_target(self, name):
        self.client.send_message("/look_at_camera_target", name)

    def load_targets(self):
        self.targets = self.send_get_saved_camera_targets()

    def send_look_around(self, test):
        self.client.send_message("/look_around", [])

    def send_delete_camera_target(self, name):
        self.client.send_message("/delete_camera_target", [name])



    # RUN SERVER #############################################################
    
    async def run_server(self):
    
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.default_handler)
        server = AsyncIOOSCUDPServer((self.gui_ip, self.gui_port), dispatcher, asyncio.get_event_loop())
        _, _ = await server.create_serve_endpoint()
     
        osc_app = OSCApp(osc_server=self)
        asyncio.ensure_future(osc_app.async_run(async_lib='asyncio'))
        self.send_get_saved_camera_targets()
        print("Server started successfully. Waiting for messages...")

        await asyncio.get_event_loop().create_future()


# GUI ###################################################################################################################

class OSCApp(App):
    def __init__(self, osc_server=None, **kwargs):
        super().__init__(**kwargs)
        self.osc_server = osc_server
        if self.osc_server:
            self.osc_server.send_stop_chat_controller("")

        Window.bind(on_request_close=self.on_request_close)
        self.chat_controller_active = False  
        self.manual_listen_enabled = False
        self.asr_paused = False

    def build(self):

        self.main_layout = BoxLayout(orientation='horizontal')
 
        self.column1 = BoxLayout(orientation='vertical', width=200)
        self.column2 = BoxLayout(orientation='vertical', width=200)
        self.column4 = BoxLayout(orientation='vertical', width=200)
        
        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        self.column2.add_widget(Label(text='TTS', size_hint_y=None, height=30))

        self.main_layout.add_widget(self.column1)
        self.main_layout.add_widget(self.column2)
        self.main_layout.add_widget(self.column4)
        
  
        self.add_column1_buttons()
       
        
        return self.main_layout
    
    def on_request_close(self, *args, **kwargs):

        self.stop_asyncio_loop()
        return False  

    def stop_asyncio_loop(self):
        loop = asyncio.get_event_loop()
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    def add_column1_buttons(self):
        
        start_chat_btn = Button(text="Start Chat Controller", on_press=self.toggle_chat_controller)
        self.column1.add_widget(start_chat_btn)

    
    def toggle_chat_controller(self, instance):
        self.chat_controller_active = not self.chat_controller_active
        
        self.column1.clear_widgets()
        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        
        if self.chat_controller_active:
            self.osc_server.send_start_chat_controller("")
            btn = Button(text="Stop Chat Controller", on_press=self.toggle_chat_controller)
            self.column1.add_widget(btn)
           
            self.add_enable_manual_listen_button()
            self.add_pause_asr_button()
        
        else:
            self.osc_server.send_stop_chat_controller("")
            btn = Button(text="Start Chat Controller", on_press=self.toggle_chat_controller)
            self.column1.add_widget(btn)
            self.manual_listen_enabled = False 


    def add_enable_manual_listen_button(self):
    
        enable_listen_btn = Button(text="Enable Manual Listen", on_press=self.toggle_manual_listen)
        self.column1.add_widget(enable_listen_btn)

    def toggle_manual_listen(self, instance):
        self.manual_listen_enabled = not self.manual_listen_enabled
        
        self.update_chat_buttons()


    def update_chat_buttons(self):
       
        self.column1.clear_widgets()
        self.column1.add_widget(Label(text='Chat', size_hint_y=None, height=30))
        if self.chat_controller_active:
            self.column1.add_widget(Button(text="Stop Chat Controller", on_press=self.toggle_chat_controller))
        else:
            self.column1.add_widget(Button(text="Start Chat Controller", on_press=self.toggle_chat_controller))
        
       
        if self.manual_listen_enabled:
            self.column1.add_widget(Button(text="Disable Manual Listen", on_press=self.toggle_manual_listen))
            self.column1.add_widget(Button(text="Stop Listening", on_press=self.osc_server.send_stop_listen))
            self.osc_server.send_enable_listen(None)  
        else:
            self.add_enable_manual_listen_button()
            self.osc_server.send_disable_listen(None) 

        if self.asr_paused:
            self.column1.add_widget(Button(text="Resume ASR", on_press=self.toggle_asr))
            self.osc_server.send_pause_asr(None)  
        else:
            self.add_pause_asr_button()
            self.osc_server.send_resume_asr(None) 

    def add_pause_asr_button(self):
        pause_asr_btn = Button(text="Pause ASR", on_press=self.toggle_asr)
        self.column1.add_widget(pause_asr_btn)

    def toggle_asr(self, instance):
        self.asr_paused = not self.asr_paused
        
        self.update_chat_buttons()

    def add_column2_buttons(self):
        welcome_tts_btn = Button(text="TTS Welcome line", on_press=self.osc_server.send_welcome_tts)
        self.column1.add_widget(welcome_tts_btn)

    def add_column4_buttons(self):

        self.column4.add_widget(Label(text='Camera Targets', size_hint_y=None, height=30))
        self.column4.add_widget(Button(text="Create new camera target", on_press=self.initiate_new_target_creation))
        self.column4.add_widget(Button(text="Look around", on_press=self.osc_server.send_look_around))
      

    def update_buttons(self, targets):
      
        self.column4.clear_widgets()  
        self.add_column4_buttons()  
        
        for target in targets:
            
            target_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44)
            
            
            target_btn = Button(text=target, size_hint_x=0.5)
            target_btn.bind(on_press=lambda instance, t=target: self.osc_server.send_look_at_camera_target(t))
            
         
            delete_btn = Button(text="Del", size_hint_x=0.25)
            delete_btn.bind(on_press=lambda instance, t=target: self.delete_target(t))
         
            target_layout.add_widget(target_btn)
            target_layout.add_widget(delete_btn)
      
            self.column4.add_widget(target_layout)

    def delete_target(self, target):
        self.osc_server.send_delete_camera_target(target)

        if target in self.osc_server.targets:
            self.osc_server.targets.remove(target)
        self.update_buttons(self.osc_server.targets)


    def show_input_popup(self, title, hint_text, send_method):
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_field = TextInput(hint_text=hint_text, size_hint_y=None, height=44)
        send_btn = Button(text='Send', size_hint_y=None, height=50)
        popup_layout.add_widget(input_field)
        popup_layout.add_widget(send_btn)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.75, 0.4))
        send_btn.bind(on_press=lambda instance: self.send_input_data(input_field.text, send_method, popup))
        popup.open()

 
    def send_input_data(self, input_data, send_method, popup):
        if input_data.strip(): 
            send_method(input_data)
            popup.dismiss()
    

    def initiate_new_target_creation(self, instance):
        self.osc_server.send_create_new_camera_target()  
        self.show_input_popup("Create New Camera Target", "Enter target name", self.osc_server.send_record_camera_target)

async def main():
    try:
        server = OSCServer()
        await server.run_server()  
    
    except KeyboardInterrupt:
        server.client.send_message("/stop_chat_controller", [])
        print("Server closed manually.")

if __name__ == "__main__":
    asyncio.run(main())

