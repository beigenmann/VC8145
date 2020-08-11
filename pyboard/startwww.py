
from microWebSrv import MicroWebSrv
from machine import UART , RTC , Timer
import machine
import json
import ntptime
import esp32


try :
	uart=UART(1,9600)
	uart.init(9600,bits=8,parity=None,stop=1,rx=13,tx=12, timeout=1000)
except : 
	print("Exception Uart")
try:
	rtc = RTC()
	ntptime.settime()
except :
	print("Exception rtp")


websocketList = []
timer = Timer(0)
timer.init(freq=5, callback=lambda t:timerEvent())
_cmd = 0
_minmax = ""
_hold =""
_rel = ""
_rangecount = 0


def timerEvent() :
	#print("Timer Event")
	global _cmd 
	if _cmd > 0 :
		values = bytearray([_cmd])
		uart.write(values)
		_cmd = 0
		return
	if len(websocketList) > 0 :
		dict = {}
		ret = _readuart(0x89,dict) 
		ret = _readuart(0x8b,dict) 
		ret = _readuart(0x8a,dict) 
		dict['internal'] = round((esp32.raw_temperature()-32)*5/9,1) # Read ESP32 internal temp
		try:
			dict['time'] = rtc.datetime()  # Record current time
		except:
			 dict['time'] = "0"
		dictfirst = dict["first"]
		dictsecond = dict["second"]
		if dictfirst["mode"] == "Diode":
			if dictfirst["realvalue"] > 3.1:
				dictsecond["value"] = "open"
			else :
				dictsecond["value"] = "shrt"
		for i, webSocket in enumerate(websocketList):
			webSocket.SendText(""+json.dumps(dict))
	


# ----------------------------------------------------------------------------

@MicroWebSrv.route('/test')
def _httpHandlerTestGet(httpClient, httpResponse) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>TEST GET</title>
        </head>
        <body>
            <h1>TEST GET</h1>
            Client IP address = %s
            <br />
			<form action="/test" method="post" accept-charset="ISO-8859-1">
				First name: <input type="text" name="firstname"><br />
				Last name: <input type="text" name="lastname"><br />
				<input type="submit" value="Submit">
			</form>
        </body>
    </html>
	""" % httpClient.GetIPAddr()
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )


@MicroWebSrv.route('/test', 'POST')
def _httpHandlerTestPost(httpClient, httpResponse) :
	formData  = httpClient.ReadRequestPostedFormData()
	firstname = formData["firstname"]
	lastname  = formData["lastname"]
	content   = """\
	<!DOCTYPE html>
	<html lang=en>
		<head>
			<meta charset="UTF-8" />
            <title>TEST POST</title>
        </head>
        <body>
            <h1>TEST POST</h1>
            Firstname = %s<br />
            Lastname = %s<br />
        </body>
    </html>
	""" % ( MicroWebSrv.HTMLEscape(firstname),
		    MicroWebSrv.HTMLEscape(lastname) )
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )


@MicroWebSrv.route('/edit/<index>')             # <IP>/edit/123           ->   args['index']=123
@MicroWebSrv.route('/edit/<index>/abc/<foo>')   # <IP>/edit/123/abc/bar   ->   args['index']=123  args['foo']='bar'
@MicroWebSrv.route('/edit')                     # <IP>/edit               ->   args={}
def _httpHandlerEditWithArgs(httpClient, httpResponse, args={}) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>TEST EDIT</title>
        </head>
        <body>
	"""
	content += "<h1>EDIT item with {} variable arguments</h1>"\
		.format(len(args))
	
	if 'index' in args :
		content += "<p>index = {}</p>".format(args['index'])
	
	if 'foo' in args :
		content += "<p>foo = {}</p>".format(args['foo'])
	
	content += """
        </body>
    </html>
	"""
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )

# ----------------------------------------------------------------------------

def _acceptWebSocketCallback(webSocket, httpClient) :
	print("WS ACCEPT")
	webSocket.RecvTextCallback   = _recvTextCallback
	webSocket.RecvBinaryCallback = _recvBinaryCallback
	webSocket.ClosedCallback 	 = _closedCallback
	websocketList.append(webSocket)
	

def _recvTextCallback(webSocket, msg) :
	print("WS RECV TEXT : %s" % msg)
	switcher = {
		"auto_range": 0xA0,
		"range": 0xA1,
		"2nd_view": 0xA3,
		"no_hold": 0xA4,
		"hold": 0xA5,
		"no_rel": 0xA6,
		"rel": 0xA7,
		"no_min_max": 0xA8,
		"min_max": 0xA9,
		"disable_rs232": 0xAA, 
		"timer": 0xAB,
		"select": 0xAD,
    }
	global _cmd
	global _minmax
	global _hold
	global _rel
	global _rangecount
	if msg == "min_max" and _minmax == "avg":
		msg = "no_min_max"
		print("Convert : %s" % msg)
	if msg == "hold" and _hold == "PH-":
		msg = "no_hold"
		print("Convert : %s" % msg)
	if msg == "rel" and _rel == "rel":
		msg = "no_rel"
		print("Convert : %s" % msg)
	if msg == "range" :
		if _rangecount > 3 :
			msg = "auto_range"
			_rangecount = 0
		else :
			_rangecount = _rangecount + 1
		print("Convert : %s" % msg)
	_cmd = switcher.get(msg, 0)
	
	

	
def _recvBinaryCallback(webSocket, data) :
	print("WS RECV DATA : %s" % data)

def _closedCallback(webSocket) :
	websocketList.remove(webSocket)
	print("WS CLOSED")


def _readuart (cmd, _dictret) :
	values = bytearray([cmd])
	uart.write(values)
	ar = uart.readline()
	return _parseDeviceMode(ar,_dictret)

def _parseDeviceMode( ar, _dictret):
	switcher = {
		0x00: 1,
		0x08: 2,
		0x10: 3,
		0x18: 4,
		0x20: 5,
		0x28: 6 
    } 
	dict = {}
	b0 = ar[0]
	b1 = ar[1]
	b2 = ar[2]
	range_ = b2 & 0x38
	dpp = switcher.get(range_, 0)
	#dict['raw'] = str(ar)
	mode = b1 & 0b11111000
	#dict['rawmode'] = mode
	#dict['dpp'] = dpp 
	dict['pre_unit'] = ""
	dict['unit'] = ""
	if mode == 0xa0 :
		dict['mode'] = "Generator"
	if mode == 0xd0 :
		dict['mode'] = "Frequency"
		dict['unit'] = "Hz"
		if  dpp == 3 or dpp == 4 or dpp == 5:
			dict['pre_unit'] = "k"
			dpp -= 3
		if dpp == 6 :
			dpp -= 6
			dict['pre_unit'] = "M"
	if mode == 0xc8 :
		dict['mode'] = "Capacitance"
		dict['unit'] = "F"
		if dpp < 4 :
			dict['pre_unit'] = "n"
			dpp -= 1
		else :
			dpp -= 4
			dict['pre_unit'] = "µ"
	if mode == 0xc0 :
		dict['mode'] = "Temperature"
		if b0 == 0x89 :
			dict['unit'] = "℃"
		else :
			dpp += 1
			dict['unit'] = "℉"
	if mode == 0xd8 :
		dict['mode'] = "Diode"
		dpp -= 1
		dict['unit'] = "V"
	if mode == 0xe0 :
		dict['mode'] = "Resistance"
		dict['unit'] = "Ω"
		if dpp == 1 :
			dpp+=1
		elif dpp == 5 or dpp == 6 :
			dpp -= 5
			dict['pre_unit'] = "M"
		else:
			dpp -= 2
			dict['pre_unit'] = "k"
	if mode == 0xa8 :
		dict['mode'] = "Current"
		dpp -= 1
		dict['unit'] = "A"
	if mode == 0xb0 :
		dict['mode'] = "Current"
		dict['unit'] = "A"
		dict['pre_unit'] = "m"
	if mode == 0xe8 :
		dict['mode'] = "Voltage"
		dict['unit'] = "V"
		dict['pre_unit'] = "m"
	if mode == 0xf8 :
		dict['mode'] = "Voltage AC"
		dpp -= 1
		dict['unit'] = "V"
	if mode == 0xf0 :
		dict['mode'] = "Voltage DC"
		dpp -= 1
		dict['unit'] = "V"
	
	select = b1 & 0b11
	#dict['select'] = select 
	b2 = ar[2]
	autorange = b2 >> 6 & 0b1
	lautorange = "auto"
	if autorange == 0 :
		lautorange = "man"
	dict['autorange'] = lautorange
	
	secondView = b2  & 0b111
	dict['secondView'] = secondView
	b3 = ar[3]	
	minmax = (b3 >> 3 ) & 0b1111
	lminmax = ""
	if minmax == 0x0:
		lminmax = ""
	if minmax == 0x8:
		lminmax = "max"
	if minmax == 0x9:
		lminmax = "min"
	if minmax == 0xa:
		lminmax = "max-min"
	if minmax == 0xb:
		lminmax = "avg"
	dict['minmax'] = lminmax
	
	rel = b3 & 0b11
	lrelative = ""
	if rel == 2 :
		lrelative = "rel"
	dict['rel'] = lrelative
	
	
	b4 = ar[4]
	sign = (b4 >> 4) & 0b111
	dict['sign'] =""
	if sign == 0 :
		dict['sign'] =""
	if sign == 1 :
		dict['sign'] ="-"
	if sign == 4 : 
		dict['sign'] = "" 
	if sign == 5 :	
		dict['sign'] = "-"
	rangef = (b4 >> 2) & 0b11
	dict['range'] = rangef
	hold = b4  & 0b11
	lhold = ""
	if hold == 0:
		lhold = "" 
	if hold == 1:
		lhold = "A-H"
	if hold == 2:
		lhold= "PH%"
	if hold == 3:
		lhold = "PH-"
	dict['hold'] = lhold
	
	
	if b0 == 0x8b or  b0 == 0x89 :
		value = ar[5:10].decode("utf-8")
		if value == "??0>?" :
			value = " .OL  "
		elif dpp < 4  and value != "?????":
			insert = dpp +1 
			value = value[:insert] + "." + 	value[insert:]
			fl = float(value)
			if dict['pre_unit']  == "k":
				fl = fl * 1000
			if dict['pre_unit']  == "M":
				fl = fl * 1000000
			if dict['pre_unit']  == "m":
				fl = fl * 0.000001
			if dict['pre_unit']  == "µ":
				fl = fl * 0.000000001
			if dict['pre_unit']  == "n":
				fl = fl * 0.001
			dict['realvalue'] =  fl
		dict['value'] =  value
	#	dict['unknown'] = hex(ar[10])
	if b0 == 0x8a :
		dict['value'] = ar[6]
		_dictret["status"] = dict
	if b0 == 0x89 :
		_dictret["first"] = dict
		global _minmax
		global _hold
		global _rel
		_minmax = lminmax
		_hold = lhold
		_rel = lrelative
	if b0 == 0x8b :
		_dictret["second"] = dict
	return _dictret


# ----------------------------------------------------------------------------

#routeHandlers = [
#	( "/test",	"GET",	_httpHandlerTestGet ),
#	( "/test",	"POST",	_httpHandlerTestPost )
#]
srv = MicroWebSrv(webPath='www/')
srv.MaxWebSocketRecvLen     = 256
srv.WebSocketThreaded		= True
srv.AcceptWebSocketCallback = _acceptWebSocketCallback
srv.Start(threaded=True)




# ----------------------------------------------------------------------------
