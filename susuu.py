import sys
from decimal import Decimal, InvalidOperation

class SusuGroup:
    def __init__(self, weekly_contribution: float or Decimal):
        try:
            self.weekly_contribution = Decimal(str(weekly_contribution))
        except InvalidOperation:
            raise ValueError("Invalid contribution amount format.")
            
        if self.weekly_contribution <= 0:
            raise ValueError("Weekly contribution must be greater than zero.")
        
        self.members = []  # Order preserved for rotation
        self.current_week = 1
        
        # Tracking states
        self.balances = {}       # {member_id: Decimal(paid_this_week)}
        self.payout_history = []  # list of dicts: {"week": int, "member": str, "amount": Decimal}
        self.has_started = False  # Locks member additions once tracking begins

    def add_member(self, member_id: str):
        member_id = member_id.strip()
        if not member_id:
            raise ValueError("Member name or ID cannot be empty.")
        if self.has_started:
            raise ValueError("Cannot add members after the tracking tracking has started.")
        if member_id in self.members:
            raise ValueError(f"Member '{member_id}' already exists.")
        
        self.members.append(member_id)
        self.balances[member_id] = Decimal("0.00")

    def record_contribution(self, member_id: str, amount: float or Decimal):
        self.has_started = True
        if member_id not in self.balances:
            raise ValueError(f"Unknown member: '{member_id}'.")
        
        try:
            amount_dec = Decimal(str(amount))
        except InvalidOperation:
            raise ValueError("Invalid payment amount format.")
            
        if amount_dec <= 0:
            raise ValueError("Contribution amount must be greater than zero.")
            
        already_paid = self.balances[member_id]
        remaining_owed = self.weekly_contribution - already_paid
        
        if amount_dec > remaining_owed:
            raise ValueError(
                f"Payment exceeds remaining obligation. {member_id} owes {remaining_owed} GHS, "
                f"but tried to pay {amount_dec} GHS."
            )
            
        self.balances[member_id] += amount_dec

    def close_week(self):
        if not self.members:
            raise ValueError("Cannot close a week with zero members.")
            
        self.has_started = True
        
        # Check if everyone paid in full
        arrears = {}
        for m in self.members:
            owed = self.weekly_contribution - self.balances[m]
            if owed > 0:
                arrears[m] = owed
                
        if arrears:
            report_str = ", ".join([f"{m} owes {amt:.2f} GHS" for m, amt in arrears.items()])
            return False, f"Week {self.current_week} cannot close. Arrears: {report_str}."
            
        # Payout logic
        pot_size = self.weekly_contribution * len(self.members)
        payout_index = (self.current_week - 1) % len(self.members)
        recipient = self.members[payout_index]
        
        self.payout_history.append({
            "week": self.current_week,
            "member": recipient,
            "amount": pot_size
        })
        
        msg = f"Week {self.current_week} closed successfully! Pot of {pot_size:.2f} GHS paid to {recipient}."
        
        # Transition to next week
        self.current_week += 1
        for m in self.members:
            self.balances[m] = Decimal("0.00")
            
        return True, msg

    def get_report(self):
        paid_in_full = []
        owes_what = {}
        
        for m in self.members:
            paid = self.balances[m]
            owed = self.weekly_contribution - paid
            if owed == 0:
                paid_in_full.append(m)
            else:
                owes_what[m] = owed
                
        return {
            "current_week": self.current_week,
            "paid_in_full": paid_in_full,
            "owes_what": owes_what,
            "payout_history": self.payout_history
        }

def run_menu():
    print("--- Welcome to Susu Tracker ---")
    try:
        contrib = input("Enter fixed weekly contribution (GHS): ")
        group = SusuGroup(contrib)
    except Exception as e:
        print(f"Error initializing group: {e}")
        return

    while True:
        print(f"\n=== WEEK {group.current_week} MENU ===")
        print("1. Add Member")
        print("2. Record Contribution")
        print("3. Close Week")
        print("4. Show Report")
        print("5. Exit")
        
        choice = input("Select an option (1-5): ").strip()
        
        if choice == '1':
            name = input("Enter unique member name/ID: ")
            try:
                group.add_member(name)
                print(f"Added member: {name}")
            except ValueError as e:
                print(f"Error: {e}")
                
        elif choice == '2':
            name = input("Enter member name/ID: ")
            amt = input("Enter contribution amount (GHS): ")
            try:
                group.record_contribution(name, amt)
                print(f"Successfully recorded {amt} GHS for {name}")
            except ValueError as e:
                print(f"Error: {e}")
                
        elif choice == '3':
            success, msg = group.close_week()
            print(msg)
            
        elif choice == '4':
            rep = group.get_report()
            print(f"\n--- Report (Week {rep['current_week']}) ---")
            print(f"Paid in Full: {', '.join(rep['paid_in_full']) if rep['paid_in_full'] else 'None'}")
            print("Owes What:")
            if rep['owes_what']:
                for m, amt in rep['owes_what'].items():
                    print(f"  - {m}: owes {amt:.2f} GHS")
            else:
                print("  - Nobody owes anything!")
            print("Payout History:")
            if rep['payout_history']:
                for p in rep['payout_history']:
                    print(f"  - Week {p['week']}: {p['amount']:.2f} GHS paid to {p['member']}")
            else:
                print("  - No payouts recorded yet.")
                
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid selection. Try again.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--menu":
        run_menu()
