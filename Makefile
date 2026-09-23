install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m unittest discover -s tests -v

buy: 
	python3 controller.py buy

check:
	python3 controller.py check

buy_lotto:
	python3 controller.py buy_lotto

buy_win720:
	python3 controller.py buy_win720

check_lotto:
	python3 controller.py check_lotto

check_win720:
	python3 controller.py check_win720
