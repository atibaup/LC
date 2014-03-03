import datetime as dt
import calendar
from dateutil.relativedelta import relativedelta
import sys
sys.path.append('/Users/apuig/Documents/Projects/lendingclubchecker')
from lendingclub import *

class Note:
   def __init__(self, principal, interest, term, start=dt.date.today(), fee=0.01):
      self.P= principal
      self.I= float(interest)/(12*100)
      self._interest = interest
      self.term = term
      self.start = start
      self.fee = fee

   def __str__(self):
       note_str = 'Principal: %.2f\n' % self.P
       note_str += 'Interest: %.2f%% (monthly: %.2f%%)\n' % (self._interest, self.I*100.)
       note_str += 'Term: %.2f\n' % self.term
       note_str += 'Start: %s' % str(self.start)
       return note_str

   def __repr__(self):
       return self.__str__()

   def annuity(self):
      P = self.P
      I = self.I
      n = self.term
      return P*(I + float(I)/((1+I)**n -1))

   def date(self, t):
      '''
      Returns date of t-th payment
      '''
      return self.start + relativedelta(months = t)

   def principal(self, t):
      '''
      Amount of principal paid at the t-th payment
      '''
      return self.annuity() - self.interest(t)

   def interest(self, t):
      '''
      Amount of interest paid at the t-th payment
      '''
      return self.principal_balance(t)*self.I

   def principal_balance(self, t):
      '''
      Principal balance after payment number t:

      p(t) = p(t-1)*r - A = P*r^t - A * (r^t - 1)/(r - 1)
      '''
      P = self.P
      I = self.I
      r = 1 + I
      A = self.annuity()
      return P*(r**t) - A*float(r**t-1)/(r-1)

   def interest_balance(self, t, rel=False):
      '''
      Interest balance after the t-th payment:

      I(t)/p(t) = i*(p(t) + p(t+1) + ... + p(n))/p(t)
      '''
      if t==self.term:
          return 0.
      int_balance = self.annuity()*(self.term-t) - self.principal_balance(t) 
      if rel == True:
         return int_balance/self.principal_balance(t) 
      else:
         return int_balance

   def schedule(self, t=0):
      '''
      Returns amortization schedule for note
      '''
      A = self.annuity()
      print 'n\tdate\t\tP\tI\tA\tP(B)\tI(B)'
      for i in xrange(t, self.term):
        print '%d\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f' % (i+1, self.date(i), self.principal(i), 
                                                        self.interest(i), A,
                                                        self.principal_balance(i+1),
                                                        self.interest_balance(i+1))
   
   def accrued_interest_at_t(self, t, year, month_num, n_days):
       '''
       Accrued interest n_days after t-th payment:

       Accrued Interest = p(t) * interest * (n_days/daysInMonth) 
       '''
       days_in_month = calendar.monthrange(year, month_num)[1]
       return self.principal_balance(t)*self.I*float(n_days)/days_in_month

   def face_value_at_t(self, t, year, month_num, n_days):
       '''
       Returns face value of note after the t-th payment: principal + accrued interest
       '''
       return self.principal_balance(t) + self.accrued_interest_at_t(t, year, month_num, n_days)

   def returns_at_maturity_at_t(self, t, year, month_num, n_days):
       '''
       Returns total return if note held until maturity:

       returns = (1 - fee)*(principal_balance(t) + interest_balance(t) + accrued_interest(...))
       '''
       returns = (1. - self.fee) * (self.principal_balance(t) + self.interest_balance(t) \
               + self.accrued_interest_at_t(t, year, month_num, n_days))
       return returns

   def ROI_at_t(self, t, year, month_num, n_days, price=None):
       '''
       Returns investment returns from note at the t-th payment plus n_days, discounting fee
       '''
       if price is None:
           price = self.face_value_at_t(t, year, month_num, n_days)
       return (self.returns_at_maturity_at_t(t, year, month_num, n_days) - price)/price *100

   def from_date_to_t(self, date):
       '''
       Returns payment number at date, and year, month and number of days since last payment at date
       '''
       for t in xrange(self.term):
           if date <= self.date(t):
               break
       return t-1, date.year, date.month, date.day - self.date(t).day

   def face_value(self, date=dt.date.today()):
       '''
       Returns face value of note at date
       '''
       t, y, m, n = self.from_date_to_t(date)
       return self.face_value_at_t(t, y, m, n)

   def ROI(self, date=dt.date.today(), price=None):
       '''
       Returns investment returns from note at date, discounting fee
       
       Arguments
       --------
       date: datetime.date, default today
       price: float, default Note.face_value
       '''
       t, y, m, n = self.from_date_to_t(date)
       return self.ROI_at_t(t, y, m, n, price)

   def remaining_payments(self, P_balance):
       '''
       Returns number of remaining payments based on given principal balance
       '''
       for t in xrange(self.term):
           if P_balance >= self.principal_balance(t):
               return self.term - t

class LendingClubNote(Note):
    '''
    An extension of Note to the specifics of Lending Club note
    '''
    def __init__(self, loan_id, note_id, order_id, principal, interest, grade, term, start=dt.date.today(), fee=0.01, **kwargs):
        '''
        Call: LendingClubNote(loan_id, note_id, order_id, principal, interest, term, start=dt.date.today(), fee=0.01)
        '''
        Note.__init__(self, principal, interest, term, start, fee)
        self.loan_id = loan_id
        self.note_id = note_id
        self.order_id = order_id
        self.grade = grade
        self.collection_log = kwargs.get('collection_log', None)
        self.payment_history = kwargs.get('payment_history', None)
        self.credit_history = kwargs.get('credit_history', None)
        
    @classmethod
    def from_website(cls, loan_id, note_id, order_id, lc_browser = None):
        '''

        '''
        from urllib import urlopen
        note_url = 'https://www.lendingclub.com/account/loanPerf.action?loan_id=%d&order_id=%d&note_id=%d' % (
                                loan_id, order_id, note_id)
        print 'Attempting to retrieve note details from %s' % note_url
        if lc_browser is None:
            lc_browser = LendingClubBrowser()
        lc_browser.login()
        soup = BeautifulSoup(lc_browser.browser.open(note_url).read())
        
        credit_history = extract_credit_history(soup)
        collection_log = extract_collection_log(soup)
        payment_history = extract_payment_history(soup)
        start_date, principal, grade, interest, term = extract_note_info(soup)
        return cls(loan_id, note_id, order_id, principal, interest, grade, term, start_date, collection_log = collection_log,
                 credit_history = credit_history, payment_history = payment_history)


def extract_note_info(soup):
    note_details = [extract_row(r) for a in soup.findAll('div', {'id': 'object-details'}) for r in a.findAll('table')][0]  
    start_date = parsedate(note_details[0])
    principal = int(note_details[1].split('$')[1])
    grade = note_details[3].split('&nbsp;:&nbsp;')[0]
    interest = float(re.sub('%', '', note_details[3].split('&nbsp;:&nbsp;')[1]))
    term = int(note_details[4].split('&nbsp;&nbsp;')[0])
    return start_date, principal, grade, interest, term



