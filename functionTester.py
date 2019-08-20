def commaSeparatedNum(num):
	numList = list(str(num))
	counter = 1
	numCommas = 0

def commaSeparatedNum(num): # TODO: make this function take into account decimal places or standardize the way decimal places are handled
	numList = list(format(num,'0.2f'))
	counter = 1
	numCommas = 0

	for i in range(0,len(numList) - 4): # -4 to take into account decimal and padding
		if counter % 3 == 0:
			numList.insert(len(numList) - 4 - i - numCommas, ',')
			counter = 1
			numCommas = numCommas + 1
			continue

		counter = counter + 1

	return "".join(numList)

print commaSeparatedNum(2148921976867)