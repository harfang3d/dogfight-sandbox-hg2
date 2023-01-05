import socket
import struct
import threading, sys

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

message_buffer = {}
send_message_thread = None
condition = threading.Condition()
logger = ""
sock = 0


def broadcast_msg(msg, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.sendto(msg, ("<broadcast>", port))


def connect_socket(c_host, port):
	global sock

	# Create a socket (SOCK_STREAM means a TCP socket)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# Connect to server and send data
	while (1):
		try:
			return sock.connect((c_host, port)) == 0
		except:
			pass


def listener_socket(port_):
	global sock, logger
	if sock != 0:
		sock.close()
	# Create a socket (SOCK_STREAM means a TCP socket)
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((HOST, port_))
	server_socket.listen(1)
	sock, address = server_socket.accept()
	logger = "{} connected".format(address)


def close_socket():
	sock.close()


def check_send_message(cv):
	while 1:
		with cv:
			cv.wait()
			m = message_buffer
			# create header with id of the binding function and the length of the message
			values = (m["id"], len(m["m"]))
			packer = struct.Struct('hi')
			packed_data = packer.pack(*values)

			sock.sendall(packed_data + m["m"])


# send only the last message in the thread
def send_message_quick(id, message):
	global send_message_thread, message_buffer
	with condition:
		message_buffer = {"id": id, "m": message}
		condition.notifyAll()

	if send_message_thread is None:
		send_message_thread = threading.Thread(target=check_send_message, args=(condition,))
		send_message_thread.start()


def send_message_with_id(id, message):
	# create header with id of the binding function and the length of the message
	values = (id, len(message))
	packer = struct.Struct('hi')
	packed_data = packer.pack(*values)

	sock.sendall(packed_data + message)


def send_message(message):
	# create header with id of the binding function and the length of the message
	size = len(message)
	sizeb = size.to_bytes(4, byteorder='big')
	sock.sendall(sizeb + message)

	"""
	values = (len(message),)
	packer = struct.Struct('i')
	packed_data = packer.pack(*values)

	sock.sendall(packed_data + message)
	"""


def get_answer_header_with_id():
	received = sock.recv(8)
	if len(received) <= 0:
		return None
	state = struct.unpack('hi', received)
	return state[1]  # size of the waiting message


def get_answer_header():  # int with the length of the msg
	global logger
	try:
		received = sock.recv(4)
		while len(received) > 0 and len(received) < 4:
			received += sock.recv(4 - len(received))

		if len(received) <= 0:
			return None
		size = int.from_bytes(received, "big")
		return size  # size of the waiting message
	except Exception:
		logger = "Error: Crash socket get_answer_header\n {0}".format(sys.exc_info()[0])
		return None


def get_answer(with_id=False, max_size_before_flush=-1):
	global logger
	try:
		if with_id:
			size = get_answer_header_with_id()
		else:
			size = get_answer_header()
		if size is None or (max_size_before_flush != -1 and size > max_size_before_flush):
			return None

		received = sock.recv(size)

		while len(received) < size:
			received += sock.recv(size - len(received))

		return received
	except Exception:
		logger = "Error: Crash socket get answer\n {0}".format(sys.exc_info()[0])
		return None

