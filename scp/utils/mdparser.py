from typing import Dict


ALL_CHARS: Dict[str] = {
	'\\',
	'\'',
	'*',
	'_',
	'{',
	'}',
	'[',
	']',
	'(',
	')',
	'#',
	'+',
	'-',
	'.',
	'!',
	'`',
	'.',
	'=',
	'>',
	'<',
	'~',
	'|'
}

def escapeAny(value) -> str:
	return f"{value}"

def escapeMD(value: str) -> str:
	if not value or value == "":
		return value
	myStr = ""
	for s in value:
		if isSpecial(s):
			myStr += '\\'
		myStr += s

def isSpecial(value: str) -> bool:
	return value in ALL_CHARS
