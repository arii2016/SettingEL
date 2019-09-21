# coding: UTF-8

TRANSFER_BYTES_MAX = 256

sector=[
    {"start" : 0x08000000, "size" :  16<<10}, # sector 0
    {"start" : 0x08004000, "size" :  16<<10}, # sector 1
    {"start" : 0x08008000, "size" :  16<<10}, # sector 2
    {"start" : 0x0800C000, "size" :  16<<10}, # sector 3
    {"start" : 0x08010000, "size" :  64<<10}, # sector 4
    {"start" : 0x08020000, "size" : 128<<10}, # sector 5
    {"start" : 0x08040000, "size" : 128<<10}, # sector 6
    {"start" : 0x08060000, "size" : 128<<10}, # sector 7
    {"start" : 0x08080000, "size" : 128<<10}, # sector 8
    {"start" : 0x080A0000, "size" : 128<<10}, # sector 9
    {"start" : 0x080C0000, "size" : 128<<10}, # sector 10
    {"start" : 0x080E0000, "size" : 128<<10}, # sector 11
]

def analyze_mot_file(filename):
	print 'Reading "%s"' % filename
	f = open(filename)

	addr = []
	data = []
	start_addr = 0
	
	for line in f:
		line = line.rstrip()
		record_type = line[0:2]

		if record_type == "S0":
			continue

		elif record_type == "S1":
			n_bytes = int(line[2:4], 16)
			addr.append(int(line[4:8], 16))
			line = line[8:]
			data_line = ""
			for i in range(n_bytes-2-1):
				byte = line[i*2:i*2+2]
				data_line += chr(int(byte, 16))
			data.append(data_line)

		elif record_type == "S2":
			n_bytes = int(line[2:4], 16)
			addr.append(int(line[4:10], 16))
			line = line[10:]
			data_line = ""
			for i in range(n_bytes-3-1):
				byte = line[i*2:i*2+2]
				data_line += chr(int(byte, 16))
			data.append(data_line)

		elif record_type == "S3":
			n_bytes = int(line[2:4], 16)
			addr.append(int(line[4:12], 16))
			line = line[12:]
			data_line = ""
			for i in range(n_bytes-4-1):
				byte = line[i*2:i*2+2]
				data_line += chr(int(byte, 16))
			data.append(data_line)

		elif record_type == "S4":
			continue

		elif record_type == "S5":
			continue

		elif record_type == "S6":
			continue

		elif record_type == "S7":
			n_bytes = int(line[2:4], 16)
			start_addr = (int(line[4:12], 16))

		elif record_type == "S8":
			n_bytes = int(line[2:4], 16)
			start_addr = (int(line[4:10], 16))

		elif record_type == "S9":
			n_bytes = int(line[2:4], 16)
			start_addr = (int(line[4:8], 16))
		else:
			continue

	print "    Number of data records: %d" % len(addr)
	print "    Start address: 0x%08x" % start_addr
	f.close()

	return (addr, data, start_addr)


def reconstruct_records(addr, data):
	print "Reconstructing data records..."

	i = 0
	while i < len(addr) - 1:
		# アドレスが連続しているときはレコードをまとめる
		if addr[i] + len(data[i]) == addr[i+1]:
			# 次のレコードを現在のレコードに付け加える
			# 次のレコード全て現在のレコードに付け加えられるとき
			if len(data[i]) + len(data[i+1]) <= TRANSFER_BYTES_MAX:
				data[i] += data[i+1]
				del addr[i+1]
				del data[i+1]
			# 次のレコードの一部を現在のレコードに付け加える
			else:
				n = TRANSFER_BYTES_MAX - len(data[i])
				data[i] += data[i+1][:n]
				data[i+1] = data[i+1][n:]
				addr[i+1] += n
				i += 1
		else:
			i += 1

	print "    Number of data records: %d" % len(addr)
	return (addr, data)


def in_flash(addr):
	start_addr = 0x08000000
	end_addr = 0x08100000 - 1
	if start_addr <= addr and addr <= end_addr:
		return True
	else:
		return False


def sector_num(addr):
    start_addr = 0x08000000
    end_addr = 0x08100000 - 1
    if addr < start_addr:
        return 0
    elif addr > end_addr:
        return len(sector) - 1
    for i in range(len(sector)):
        if sector[i]["start"] <= addr and \
            addr < sector[i]["start"] + sector[i]["size"]:
            return i


def make_erase_page_list(addr, data):
    sectors = []
    # 消去が必要なセクターをチェックする
    for i in range(len(addr)):
        start_addr = addr[i]
        end_addr = addr[i] + len(data[i]) - 1
        # データ書き込み先がflash領域ではないとき
        if (not in_flash(start_addr)) and (not in_flash(end_addr)):
            continue
        # レコード1バイト目が属するセクター番号
        sector_first = sector_num(start_addr)
        # レコード最後のバイトが属するセクター番号
        sector_last = sector_num(end_addr)
        # 2つの番号間のページを消去対象にする
        for x in [sector_first + j for j in range(sector_last - sector_first + 1)]:
            if not x in sectors:
                sectors.append(x)
    return sectors
