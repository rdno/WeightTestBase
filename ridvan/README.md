# Reproduce

This is a test to reproduce Wenjie's results.


## Complex

	$ python weights.py calculate complex
	$ python weights.py analyze complex
	{u'17_40': {u'R': 0.11111111111111116,
            u'T': 0.11111111111111108,
            u'Z': 0.11111111111111113},
	'u'40_100': {u'R': 0.11111111111111113,
		     u'T': 0.1111111111111111,
             u'Z': 0.11111111111111126},
     'u'90_250': {u'R': 0.11111111111111109,
             u'T': 0.1111111111111111,
             u'Z': 0.11111111111111102}}
	Overall weights sum: 1.0

## Simple

	$ python weights.py calculate simple
	$ python weights.py analyze simple
	{u'17_40': {u'R': 0.1150089471092314,
            u'T': 0.09538653575875475,
            u'Z': 0.12613945561948142},
	u'40_100': {u'R': 0.10943760954243892,
             u'T': 0.10500082538643563,
             u'Z': 0.15429598872966713},
	u'90_250': {u'R': 0.09928318538641097,
             u'T': 0.09887480521640316,
             u'Z': 0.09657264725117885}}
	Overall weights sum: 1.0

## Simple Per Category

This is the slight change version of simple. In this version,
normalization coefficient is calculated per category. This ensure the
balanced weight across categories.

	$ python weights.py calculate simple_per_cat
	$ python weights.py analyze simple
	{u'17_40': {u'R': 0.11111111111111104,
            u'T': 0.1111111111111111,
            u'Z': 0.11111111111111108},
     u'40_100': {u'R': 0.11111111111111108,
             u'T': 0.11111111111111112,
             u'Z': 0.11111111111111077},
     u'90_250': {u'R': 0.11111111111111105,
             u'T': 0.1111111111111111,
             u'Z': 0.11111111111111101}}
	Overall weights sum: 1.0
