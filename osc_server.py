import asyncio
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient


UTILS = system.import_library("../HB3/utils.py")

# Update with IP of machine running gui
GUI_IP = "192.168.101.111"
GUI_PORT = 54321

# Update with robot ip
ROBOT_IP = "192.168.101.103"
ROBOT_PORT = 12345


class Activity:
    transport = None

    def on_message(self, channel, message):
        if channel == "send_camera_targets":
            self.client.send_message("/send_camera_targets", message)

    async def on_start(self):
        self.client = SimpleUDPClient(GUI_IP, GUI_PORT)
        UTILS.start_other_script(system, "./camera_targets.py")

        def default_handler(addr, *args):
            print(f"OSC Message {addr!r}", repr(args))

            ####################################################################################################################
            # START/STOP CHAT

            if addr == "/start_chat_controller":
                UTILS.start_other_script(system, "../HB3/Chat_Controller.py")

            elif addr == "/stop_chat_controller":
                system.messaging.post("disable_manual_mode", None)
                UTILS.stop_other_script(system, "../HB3/Chat_Controller.py")

            elif addr == "/welcome_tts":
                system.messaging.post(
                    "tts_say",
                    [
                        "Hallo zusammen, es freut mich, euch alle zu dem be more Event 2024 begrüßen zu dürfen. Ich bin nicht alleine auf der Bühne, bitte begrüßen Sie mit mir Vorstandmitglied und CEO der Group Technology, Thomas Schmall.",
                        "DE",
                    ],
                )

            ####################################################################################################################
            # SPEECH RECOGNITION Control
            elif addr == "/pause_asr":
                system.messaging.post("pause_asr", None)

            elif addr == "/resume_asr":
                system.messaging.post("resume_asr", None)

            elif addr == "/enable_manual_listen_mode":
                system.messaging.post("enable_manual_mode", None)

            elif addr == "/disable_manual_listen_mode":
                system.messaging.post("disable_manual_mode", None)

            elif addr == "/stop_listening":
                system.messaging.post("manual_mode_stop_listening", None)

            ######################################################################################################################
            # GAZE CONTROL

            elif addr == "/new_camera_target_mode":
                system.messaging.post("clear_contributor", None)
                UTILS.start_other_script(system, "../Telepresence/main.py")

                UTILS.stop_other_script(
                    system, "../HB3/Human_Animation/Add_Look_Around.py"
                )
                UTILS.stop_other_script(system, "../HB3/Look_At/Add_Glances.py")
                UTILS.stop_other_script(system, "../HB3/Perception/Process_Faces.py")

            elif addr == "/record_camera_target":
                name = args[0]

                system.messaging.post("record_camera_target", name)
                UTILS.start_other_script(
                    system, "../HB3/Human_Animation/Add_Look_Around.py"
                )
                UTILS.start_other_script(system, "../HB3/Look_At/Add_Glances.py")

            elif addr == "/look_at_camera_target":
                """
                Sends position name to Camera_Look to create contributor
                """
                system.messaging.post("look_at_camera_target", args[0])

            elif addr == "/get_camera_targets":
                print("OSC message get camera target names")
                system.messaging.post("get_camera_target_names", None)

            elif addr == "/look_around":
                """
                Full range look around
                """
                system.messaging.post("resume_look_around", None)

            elif addr == "/delete_camera_target":
                name = args[0]
                system.messaging.post("delete_target", name)

            #####################################################################################################################

        # SERVER STUFF
        dispatch = dispatcher.Dispatcher()

        dispatch.set_default_handler(default_handler)

        server = osc_server.AsyncIOOSCUDPServer(
            (ROBOT_IP, ROBOT_PORT), dispatch, asyncio.get_event_loop()
        )
        (
            self.transport,
            self.protocol,
        ) = await server.create_serve_endpoint()

    def on_stop(self):
        if self.transport:
            self.transport.close()
        UTILS.stop_other_script(system, "./camera_targets.py")
