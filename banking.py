import secrets
import sqlite3


conn = sqlite3.connect("card.s3db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS card 
            (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
            number TEXT NOT NULL UNIQUE,
            pin TEXT NOT NULL,
            balance INTEGER DEFAULT 0 NOT NULL);''')
conn.commit()

# c.execute("DROP TABLE card")

global current_card


class BankSystem:
    def __init__(self, iin="400000"):
        self.main_menu = "\n1. Create an account\n"\
                         "2. Log into account\n"\
                         "0. Exit\n" \
                         "> "
        self.cc_menu = "\n1. Balance\n"\
                       "2. Add income\n"\
                       "3. Do transfer\n"\
                       "4. Close account\n"\
                       "5. Log out\n"\
                       "0. Exit\n" \
                       "> "
        self.acc_n = secrets.SystemRandom().randint(100000000, 999999999)
        self.c_pass = secrets.SystemRandom().randint(1000, 9999)
        self.pre_generator = iin + str(self.acc_n)
        self.check_sum_digit = None
        self.c_num = None
        self.exit = False

    def luhn(self):
        odd_indexes = [int(n) * 2 if count % 2 != 0 else int(n) for count, n in enumerate(self.pre_generator, start=1)]
        over_9 = [(n - 9) if n > 9 else n for n in odd_indexes]
        result = sum(over_9)
        if result % 10 == 0:
            self.check_sum_digit = 0
        else:
            self.check_sum_digit = 10 - result % 10

    def number_generator(self):
        card_number = int(self.pre_generator + str(self.check_sum_digit))
        self.c_num = card_number

    def check_sum(self, number):
        if len(number) != 16:
            return False
        new_n = str(number)[0:15]
        odd_indexes = [int(n) * 2 if count % 2 != 0 else int(n) for count, n in enumerate(new_n, start=1)]
        over_9 = [(n - 9) if n > 9 else n for n in odd_indexes]
        result = sum(over_9) % 10
        if result == 0 and int(number[15]) == 0 or \
                (10 - result) == int(number[15]):
            return True
        return False

    def db_exists(self):
        c.execute("SELECT * FROM card")
        res = c.fetchall()
        if res:
            return True
        return False

    def db_login(self):
        global current_card
        if not self.db_exists():
            print("\nNo account has been set yet.")
        if self.db_exists():
            current_card = int(input("\nEnter your card number:")), \
                           int(input("Enter your PIN:"))
            c.execute("SELECT number, pin FROM card "
                      "WHERE number=? AND pin=?",
                      (current_card[0], current_card[1]))
            res = c.fetchall()
            if res:
                print("\nYou have successfully logged in!\n")
                return BankSystem.own_account(self)
            print("\nWrong card number or PIN!\n")

    def db_create_account(self):
        new_card = BankSystem()
        new_card.luhn()
        new_card.number_generator()
        print(new_card.c_num)
        print(new_card.c_pass)
        data = [(new_card.c_num, new_card.c_pass, 0)]
        c.executemany(f'INSERT INTO card (number,pin,balance)'
                      f' VALUES (?,?,?)', data)
        conn.commit()

    def db_balance(self):
        global current_card
        c.execute(f'SELECT balance FROM card '
                  f'WHERE number=? AND pin=?',
                  (current_card[0], current_card[1]))
        res = c.fetchone()[0]
        return f"Balance: {res}"

    def db_add_income(self):
        global current_card
        amount = int(input("Enter income:\n"))
        c.execute(f'UPDATE card SET balance=balance+? '
                  f'WHERE number=? AND pin=?',
                  (amount, current_card[0], current_card[1]))
        conn.commit()
        return "Income was added!"

    def db_transfer(self):
        global current_card
        print("\nTransfer")
        card_number_transf = input("Enter card number:\n")
        current_card_balance = c.execute(f'SELECT balance FROM card '
                                         f'WHERE number=? AND pin=?',
                                         (current_card[0], current_card[1])).fetchone()[0]
        if card_number_transf == str(current_card[0]):
            return "You can't transfer money to the same account!"
        elif not self.check_sum(card_number_transf):
            return "Probably you made mistake in the card number. Please try again!"
        try:
            c.execute(f'SELECT number FROM card '
                      f'WHERE number=?',
                      (card_number_transf,)).fetchall()[0][0]
        except IndexError:
            return "Such a card does not exist."
        transfer_amount = int(input("Enter how much money you want to transfer:\n"))
        if transfer_amount > current_card_balance:
            return "Not enough money!"
        c.execute(f'UPDATE card SET balance=balance-? '
                  f'WHERE number=? AND pin=?',
                  (transfer_amount, current_card[0], current_card[1]))
        c.execute(f'UPDATE card SET balance=balance+? '
                  f'WHERE number=?',
                  (transfer_amount, card_number_transf))
        conn.commit()
        return "Success!"

    def db_close_account(self):
        global current_card
        c.execute(f'DELETE from card '
                  f'WHERE number=? AND pin=?',
                  (current_card[0], current_card[1]))
        conn.commit()
        return "The account has been closed!"

    def db_display(self):
        c.execute('SELECT * FROM card;')
        return c.fetchall()

    def user_interface(self):
        while not self.exit:
            choice = int(input(self.main_menu))
            if choice not in [0, 1, 2]:
                print("\nUnrecognised operation.")
            elif choice == 1:
                self.db_create_account()
                print(self.db_display())
            elif choice == 2:
                self.db_login()
            elif choice == 0:
                print("Bye!")
                break

    def own_account(self):
        while True:
            choice = int(input(self.cc_menu))
            if choice not in [0, 1, 2, 3, 4, 5]:
                print("\nUnrecognised operation.")
            elif choice == 1:
                print(self.db_balance())
            elif choice == 2:
                print(self.db_add_income())
            elif choice == 3:
                print(self.db_transfer())
            elif choice == 4:
                print(self.db_close_account())
                break
            elif choice == 5:
                print("You have successfully logged out!")
                break
            elif choice == 0:
                self.exit = True
                print("Bye!")
                break


if __name__ == '__main__':
    banking_system = BankSystem()
    banking_system.user_interface()
