#!/bin/python3

import sys
import subprocess
import json
import random
import sqlite3

#Föll
#Fall sem tekur inn smileycoin-cli skipun
#ásamt argumentum og skilar úkomunni úr smileycoin skipuninni.
def smileycmd(cmd, *args):
	input = ["/home/steinar/Desktop/smileycoin-cli", cmd]
	for arg in args:
		input.append(arg)

	pipe = subprocess.Popen(input, stdout=subprocess.PIPE)
	output = pipe.stdout.read().decode("utf-8")

	return output.strip()

#STILLIBREYTUR
winning_ratio = 0.9
minimum_bet = 1000

#Það er kallað á scriptuna með txid sem argument.
txid = sys.argv[1]
#txid = "fc4025dd12fe000adce2971be41f20a2117cd78fb7163341b494885c212e93ab"

#tengjumst gagnagrunninum með öllum færslum á addressuna:
conn = sqlite3.connect('/home/steinar/smlylottery/database.db')

#Athugun hvort við höfum séð þetta transaction áður.
already_seen = tuple(conn.execute("select ? in transactions_seen as transaction_already_seen", (txid,)).fetchone())[0]
if(already_seen == 1):
	sys.exit()

conn.execute("insert into transactions_seen values(?)", (txid,))
conn.commit()

#addressan sem við erum að hlusta á:
myaddress = "BE8svSuyAuFFm1RFC8CGWXxyHCKjKBEYQW"

#náum í rawtransaction
rawtransaction = smileycmd("getrawtransaction", txid)

#decodum rawtransaction
decodedtrans = smileycmd("decoderawtransaction", rawtransaction)

#Búum til þæginlega dictionary til þess að vinna með
data = json.loads(decodedtrans)

#finnum stærð millifærslunnar sem var millifært á myaddress:
amount = 0
for output in data["vout"]:
	if(output["scriptPubKey"]["addresses"][0] == myaddress):
		amount += output["value"]

#Hættum ef ekki er lagt nóg undir
if amount < minimum_bet:
	sys.exit()

#Finnum hvaða addressa sendi:
senderAddress=None
for input in data["vin"]:
	tempn = input["vout"]
	temptransaction = smileycmd("getrawtransaction", input["txid"])
	tempdecoded = smileycmd("decoderawtransaction", temptransaction)
	tempdata = json.loads(tempdecoded)
	address = tempdata["vout"][tempn]["scriptPubKey"]["addresses"][0]

	if address != None:
		senderAddress=address
		break

#Hættum ef að sendandi fanns ekki
if address==None:
	sys.exit()

conn.execute("insert into entries values(?, ?)", (amount, senderAddress))

maxid = tuple(conn.execute("select max(rowid) from entries").fetchone())[0]

#Tékkum hvort að 10 hafi lagt inn í þennan pott.
if((maxid+1) % 10 == 0):
	#deilum út vinningum ef 10 eru komnir í pottinn.
	current_pool = conn.execute("select * from v_current_pool order by amount desc").fetchall()
	total_winnings = tuple(conn.execute("select sum(amount) from v_current_pool").fetchone())[0]

	random_number = random.randint(0, total_winnings-1)

	winning_address = "b"

	temp_sum = 0
	for row in current_pool:
		row = tuple(row)
		if(random_number >= temp_sum and random_number < temp_sum+row[1]):
			winning_address = row[2]
			break

		temp_sum += row[1]

	#Hér er búið að finna sigurvegarann
	#Tökum tíu prósent af pottinum og geymum fyrir okkur.
	#sendum restina á sigurvegarann.
	total_winnings = winning_ratio*total_winnings
	smileycmd("sendtoaddress", winning_address, str(total_winnings))

	#vistum sigurvegara í gagnagrunninum
	conn.execute("insert into winners values(?, ?, date(), time())",(winning_address, total_winnings))

conn.commit()

