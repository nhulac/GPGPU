from testcase import *

class LoadStoreTests(TestCase):
	def test_scalarLoad():
		return ({}, '''
			i10 = &label1
			i1 = mem_b[i10]
			i20 = i1 + 1			; test load RAW hazard.  Use add to ensure side effect occurs once.
			i2 = mem_b[i10 + 1]
			i3 = mem_b[i10 + 2]
			u4 = mem_b[i10 + 2]		; sign extend
			u5 = mem_b[i10 + 3]
			i6 = mem_s[i10 + 4]		; sign extend
			i21 = i6 + 1			; test load RAW hazard
			u7 = mem_s[i10 + 4]
			i8 = mem_s[i10 + 6]
			i9 = mem_l[i10 + 8]
			i22 = i9 + 1			; test load RAW hazard
			i10 = i10 + 4
			i11 = mem_b[i10 + -4]	; negative offset
			
			done goto done
			
			label1	.byte 0x5a, 0x69, 0xc3, 0xff
					.short 0xabcd, 0x1234	
					.word 0xdeadbeef
		
		''', {'u1' : 0x5a, 'u2' : 0x69, 'u3' : 0xffffffc3, 'u4' : 0xc3,
		'u5' : 0xff, 'u6' : 0xffffabcd, 'u7' : 0xabcd, 'u8' : 0x1234,
		'u9' : 0xdeadbeef, 'u10' : None, 'u20' : 0x5a + 1, 'u21' : 0xffffabcd + 1,
		'u22' : 0xdeadbeef + 1, 'u10' : None, 'u11' : 0x5a}, None, None, None)
		
	def test_scalarStore():
		baseAddr = 64
	
		return ({'u1' : 0x5a, 'u2' : 0x69, 'u3' : 0xc3, 'u4' : 0xff, 
			'u5' : 0xabcd, 'u6' : 0x1234,
			'u7' : 0xdeadbeef, 'u10' : baseAddr}, '''
	
			mem_b[i10] = i1
			mem_b[i10 + 1] = i2
			mem_b[i10 + 2] = i3
			mem_b[i10 + 3] = i4
			mem_s[i10 + 4] = i5
			mem_s[i10 + 6] = i6
			mem_l[i10 + 8] = i7
		''', {}, baseAddr, [ 0x5a, 0x69, 0xc3, 0xff, 0xcd, 0xab, 0x34, 0x12, 0xef,
				0xbe, 0xad, 0xde ], None)
	
	#
	# Store then load indivitual elements to verify endianness is correct.
	#
	def test_scalarCopy():
		baseAddr = 64
		
		return ({'u1' : 64, 'u2' : 0x12345678},
			'''
				mem_l[u1] = u2
				u3 = mem_l[u1]
				u4 = mem_s[u1]
				u5 = mem_s[u1 + 2]
				u6 = mem_b[u1]
				u7 = mem_b[u1 + 1]
				u8 = mem_b[u1 + 2]
				u9 = mem_b[u1 + 3]
			''',
			{ 'u3' : 0x12345678, 'u4' : 0x5678, 'u5' : 0x1234, 'u6' : 0x78,
				'u7' : 0x56, 'u8' : 0x34, 'u9' : 0x12 }, None, None, None)
	
	# Two loads, one with an offset to ensure offset calcuation works correctly
	# and the second instruction ensures execution resumes properly after the
	# fetch stage is suspended for the multi-cycle load.
	# We also immediately access the destination register.  Since the load
	# has several cycles of latency, this ensures the scheduler is properly 
	# inserting bubbles.
	def test_blockLoad():
		data = [ random.randint(0, 0xff) for x in range(4 * 16 * 2) ]
		v1 = makeVectorFromMemory(data, 0, 4)
		v2 = makeVectorFromMemory(data, 4, 4)
		return ({ 'u1' : 0xaaaa }, '''
			i10 = &label1
			v1 = mem_l[i10]
			v4 = v1	+ 1					; test load RAW hazard
			v6{u1} = mem_l[i10]			; mask form
			v7{~u1} = mem_l[i10]		; invert mask
			v2 = mem_l[i10 + 4]
			v5 = v2	+ 1					; test load RAW hazard
			v8{u1} = mem_l[i10 + 4]		; mask form
			v9{~u1} = mem_l[i10 + 4]	; invert mask
			done goto done
			
			label1	''' + makeAssemblyArray(data)
		, { 'v1' : v1,
			'v4' : [ x + 1 for x in v1 ],
			'v2' : v2,
			'v5' : [ x + 1 for x in v2 ],
			'v6' : [ value if index % 2 == 0 else 0 for index, value in enumerate(v1) ],
			'v7' : [ value if index % 2 == 1 else 0 for index, value in enumerate(v1) ],
			'v8' : [ value if index % 2 == 0 else 0 for index, value in enumerate(v2) ],
			'v9' : [ value if index % 2 == 1 else 0 for index, value in enumerate(v2) ],
			'u10' : None}, None, None, None)
	
	def test_blockStore():
		cases = []
		for mask, invertMask in [(None, False), (0x5a5a, False), (0x5a5a, True)]:
			baseAddr = 64
			memory = [ 0 for x in range(4 * 16 * 4) ]	
			v1 = allocateUniqueScalarValues(16)
			v2 = allocateUniqueScalarValues(16)
			emulateVectorStore(baseAddr, memory, baseAddr, v1, 4, mask, invertMask)
			emulateVectorStore(baseAddr, memory, baseAddr + 64, v2, 4, mask, invertMask)
		
			maskDesc = ''
			if mask != None:
				maskDesc += '{'
				if invertMask:
					maskDesc += '~'
					
				maskDesc += 'u1}'
			
			code = 'mem_l[i10]' + maskDesc + '''= v1
				mem_l[i10 + 64]''' + maskDesc + '''= v2
			'''
		
			cases += [ ({ 'u10' : baseAddr, 'v1' : v1, 'v2' : v2, 'u1' : mask if mask != None else 0 }, 
				code, { 'u10' : None }, baseAddr, memory, None) ]

		return cases
	
	def test_stridedLoad():
		data = [ random.randint(0, 0xff) for x in range(12 * 16) ]
		v1 = makeVectorFromMemory(data, 0, 12)
		return ({ 'u1' : 0xaaaa }, '''
			i10 = &label1
			v1 = mem_l[i10, 12]
			v2 = v1 + 1			; test load RAW hazard
			v3{u1} = mem_l[i10, 12]
			v4{~u1} = mem_l[i10, 12]
			done goto done
			label1	''' + makeAssemblyArray(data)
		, { 'v1' : v1,
			'v2' : [ x + 1 for x in v1 ],
			'v3' : [ value if index % 2 == 0 else 0 for index, value in enumerate(v1) ],
			'v4' : [ value if index % 2 == 1 else 0 for index, value in enumerate(v1) ],
			'u10' : None}, None, None, None)
	
	def test_stridedStore():
		cases = []
		for mask, invertMask in [(None, False), (0x5a5a, False), (0x5a5a, True)]:
			baseAddr = 64
			memory = [ 0 for x in range(4 * 16 * 4) ]	
			v1 = allocateUniqueScalarValues(16)
			v2 = allocateUniqueScalarValues(16)
			emulateVectorStore(baseAddr, memory, baseAddr, v1, 12, mask, invertMask)
			emulateVectorStore(baseAddr, memory, baseAddr + 4, v2, 12, mask, invertMask)
		
			maskDesc = ''
			if mask != None:
				maskDesc += '{'
				if invertMask:
					maskDesc += '~'
					
				maskDesc += 'u1}'
			
			code = 'mem_l[i10, 12]' + maskDesc + '''= v1
				i10 = i10 + 4
				mem_l[i10, 12]''' + maskDesc + '''= v2
			'''
		
			cases += [({ 'u10' : baseAddr, 'v1' : v1, 'v2' : v2, 'u1' : mask if mask != None else 0 }, 
				code, { 'u10' : None }, baseAddr, memory, None) ]
				
		return cases
	
	
	#
	# This also validates that the assembler properly fixes up label references
	# as data
	#
	def test_gatherLoad():
		labels = ['off' + str(x) for x in range(16)]
		values = allocateUniqueScalarValues(16)
		shuffledIndices = shuffleIndices()
	
		code = '''
							v0 = mem_l[ptr]
							v1 = mem_l[v0]
							v2 = v1 + 1			; test load RAW hazard
							v3{u1} = mem_l[v0]
							v4{~u1} = mem_l[v0]
				done		goto done
	
				ptr'''
	
		for x in shuffledIndices:
			code += '\t\t\t\t.word ' + labels[x] + '\n'
			
		for x in range(16):
			code += labels[x] + '\t\t\t\t.word ' + hex(values[x]) + '\n'
	
		expectedArray = [ values[shuffledIndices[x]] for x in range(16) ]
	
		return ({ 'u1' : 0xaaaa }, code, { 
			'v0' : None, 
			'v1' : expectedArray, 
			'v2' : [ x + 1 for x in expectedArray ],
			'v3' : [ value if index % 2 == 0 else 0 for index, value in enumerate(expectedArray) ],
			'v4' : [ value if index % 2 == 1 else 0 for index, value in enumerate(expectedArray) ],
			}, None, None, None)
	
	def test_scatterStore():
		baseAddr = 64
		cases = []
		for offset, mask, invertMask in [(0, None, None), 
			(8, None, None), (4, 0xa695, False), (4, 0xa695, True)]:
			memory = [ 0 for x in range(10 * 16) ]	
			values = allocateUniqueScalarValues(16)
			ptrs = [ baseAddr + x * 8 for x in shuffleIndices() ]
		
			code = 'mem_l[v1'
			if offset != None:
				code += ' + ' + str(offset)
			
			code += ']'
			if mask != None:
				code += '{'
				if invertMask:
					code += '~'
					
				code += 'u0}'	
			
			code += '=v2'
		
			emulateScatterStore(baseAddr, memory, ptrs, values, 
				offset if offset != None else 0, mask, invertMask)
		
			cases += [({ 'v1' : ptrs, 'v2' : values, 'u0' : mask if mask != None else 0}, 
				code, 
				{ 'u10' : None }, baseAddr, memory, None)]

		return cases
		
	def test_controlRegister():
		return ({ 'u7' : 0x12345}, '''
			cr7 = u7
			cr9 = u0
			u12 = cr7
		''', { 'u12' : 0x12345}, None, None, None)
		
		
		