import time
from threading import Event
import stomp
from ctakes_pbj.type_system.type_system_loader import *
from ctakes_pbj.pipeline.pbj_pipeline import STOP_MESSAGE
from ctakes_pbj.pbj_tools import arg_parser

args = arg_parser.get_args()

exit_event = Event()


def start_receiver(pipeline, queue_name=args.receive_queue, host_name=args.host_name, port_name=args.port_name,
                   password=args.password, username=args.username):
    PBJReceiver(pipeline, queue_name, host_name, port_name, password, username)
    while not exit_event.is_set():
        exit_event.wait()


class PBJReceiver(stomp.ConnectionListener):

    def __init__(self, pipeline, queue_name, host_name, port_name, password, username):
        self.source_queue = queue_name
        self.source_host = host_name
        self.source_port = port_name
        self.pipeline = pipeline
        self.password = password
        self.username = username
        self.id = '1'
        self.typesystem = None
        print(time.ctime((time.time())), "Starting PBJ Receiver on", self.source_host, self.source_queue, "...")
        # Use a heartbeat of 10 minutes  (in milliseconds)
        self.conn = stomp.Connection12([(self.source_host, self.source_port)],
                                       keepalive=True, heartbeats=(600000, 600000))
        self.conn.set_listener('PBJ_Receiver', self)
        self.stop = False
        self.__connect_and_subscribe()

    def __connect_and_subscribe(self):
        self.conn.connect(self.username, self.password, wait=True)
        self.conn.subscribe(destination=self.source_queue, id=self.id, ack='auto')
        # self.conn.subscribe(destination=self.source_queue, id=self.id, ack='client')

    def set_typesystem(self, typesystem):
        self.typesystem = typesystem

    def get_typesystem(self):
        if self.typesystem is None:
            # Load the typesystem
            type_system_accessor = TypeSystemLoader()
            type_system_accessor.load_type_system()
            self.set_typesystem(type_system_accessor.get_type_system())
        return self.typesystem

    def set_host(self, host_name):
        self.source_host = host_name

    def set_stop(self, stop):
        self.stop = stop

    def stop_receiver(self):
        self.conn.unsubscribe(destination=self.source_queue, id=self.id)
        self.conn.disconnect()
        print(time.ctime((time.time())), "Disconnected PBJ Receiver on", self.source_host, self.source_queue)
        self.pipeline.collection_process_complete()
        exit_event.set()

    def on_message(self, frame):
        if frame.body == STOP_MESSAGE:
            print(time.ctime((time.time())), "Received Stop code.")
            self.stop = True
            # time.sleep(3)
            self.stop_receiver()
        else:
            if XMI_INDICATOR in frame.body:
                cas = cassis.load_cas_from_xmi(frame.body, self.get_typesystem())
                self.pipeline.process(cas)
            else:
                print(time.ctime((time.time())), "Malformed Message:\n", frame.body)

    def on_disconnected(self):
        if self.stop is False:
            self.__connect_and_subscribe()

    def on_error(self, frame):
        print(time.ctime((time.time())), "Receiver Error:", frame.body)
