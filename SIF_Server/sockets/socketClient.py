# Echo client module
import socket
import sys
import logging
sys.path.append('.')

class sockClient:
	# The remote host    daring.cwi.nl
	HOST = socket.gethostbyname(socket.gethostname())
	PORT = 5000
	sock = None

	def __init__(self, debug=False):
		self.debug = debug
		if self.debug:
			logLevel = logging.DEBUG
		else:
			logLevel = logging.INFO
		logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)
		self.runSocket()
	def runSocket(self):
		for res in socket.getaddrinfo(self.HOST, self.PORT,
									socket.AF_UNSPEC, socket.SOCK_STREAM):
			logging.debug('''Client address info: af=%s, socktype=%s,socktype=%s,proto=%s, canonname=%s''' % res)
			af, socktype, proto, canonname, sa = res
			try:
				self.sock = socket.socket(af, socktype, proto)
			except socket.error, msg:
				print 'socket error with msg: %s' % msg
				self.sock = None
				continue
			try:
				self.sock.connect(sa)
			except socket.error, msg:
				print 'socket error with msg: %s' % msg
				self.sock.close()
				self.sock = None
				continue
			break

		if self.sock is None:
			print 'could not open socket'
			sys.exit(1)

	def sendImgStr(self, imgName = None, numrep=1):
		while numrep>0:
			img = open(imgName, 'r')
			while 1:
				line = img.readline(512)
				if not line:
					break
				self.sock.send( line )
			img.close()
			numrep -= 1
		self.sock.close()

	def sendNumArray(self, array):
		done = False
		while not done:
			line = str(array)
			if not line:
				break
			self.sock.send( line )
			done = True
		self.sock.close()

if __name__ == '__main__':
	if 'debug' in sys.argv:
		debug = True
	else:
		debug = False
	imgName = 'sockets/sky.jpg'
	client = sockClient(debug=debug)
	a = [1,2,3]
	client.sendImgStr(imgName=imgName, numrep=2)
	# client.runSocket()
	# client.sendImgStr(imgName=imgName)
	# client.sendNumArray( a )
	# client.sendNumArray( a )
