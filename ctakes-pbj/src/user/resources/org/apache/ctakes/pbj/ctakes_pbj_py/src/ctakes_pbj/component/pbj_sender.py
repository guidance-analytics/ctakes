import stomp
import time
from ctakes_pbj.component import cas_annotator
from ctakes_pbj.pipeline.pbj_pipeline import STOP_MESSAGE
from ctakes_pbj.pbj_tools import arg_parser

args = arg_parser.get_args()


class PBJSender(cas_annotator.CasAnnotator):

    def __init__(self, queue_name=args.send_queue, host_name=args.host_name, port_name=args.port_name,
                 password=args.password, username=args.username):

        self.target_queue = queue_name
        self.target_host = host_name
        self.target_port = port_name
        self.password = password
        self.username = username
        print(time.ctime((time.time())), "Starting PBJ Sender on", self.target_host, self.target_queue, "...")
        # Use a heartbeat of 10 minutes  (in milliseconds)
        self.conn = stomp.Connection12([(self.target_host, self.target_port)],
                                       keepalive=True, heartbeats=(600000, 600000))
        self.conn.connect(self.username, self.password, wait=True)

    def process(self, cas):
        print(time.ctime((time.time())), "Sending processed information to",
              self.target_host, self.target_queue, "...")
        xmi = cas.to_xmi()
        self.conn.send(self.target_queue, xmi)

    def collection_process_complete(self):
        self.send_stop()

    def send_text(self, text):
        self.conn.send(self.target_queue, text)

    def send_stop(self):
        print(time.ctime((time.time())), "Sending Stop code to", self.target_host, self.target_queue, "...")
        self.conn.send(self.target_queue, STOP_MESSAGE)
        self.conn.disconnect()
        print(time.ctime((time.time())), "Disconnected PBJ Sender on", self.target_host, self.target_queue)

    def set_queue(self, queue_name):
        self.target_queue = queue_name

    def set_host(self, host_name):
        self.target_host = host_name

    def set_port(self, port_name):
        self.target_port = port_name

    def set_password(self, password):
        self.password = password

    def get_password(self):
        return self.password

    def set_username(self, username):
        self.username = username

    def get_username(self):
        return self.username
