class Note:
   def __init__(self, principal, interest, term):
      self.P= principal
      self.I= float(interest)/100
      self.term = term

   def annuity(self):
      P = self.P
      I = self.I
      n = self.term
      return P*(I + float(I)/((1+I)**n -1))

   def principal(self, t):
      '''
      p(t) = p(t-1)*r - A = P*r^t - A * (r^t - 1)/(r - 1)
      '''
      P = self.P
      I = self.I
      r = 1 + I
      A = self.annuity()
      return P*(r**t) - A*float(r**t-1)/(r-1)

   def interest(self, t, rel=True):
      '''
      I(t)/p(t) = i*(p(t) + p(t+1) + ... + p(n))/p(t)
      '''
      if rel == True:
         return (self.annuity()*(self.term-t) - self.principal(t))/self.principal(t) 
      else:
         return self.annuity()*(self.term-t) - self.principal(t)

   def schedule(self):
      A = self.annuity()
      print 'n\tP\tI\tA'
      for i in xrange(self.term):
          print '%d\t%.2f\t%.2f\t%.2f' % (i+1,self.principal(i), self.interest(i), A)

   def remaining_payments(self, P):
      return float(P)/A

   def __str__(self):
       note_str = 'Principal: %.2f\n' % self.P
       note_str += 'Interest: %.2f%%\n' % (self.I*100.)
       note_str += 'Term: %.2f' % self.term
       return note_str

   def __repr__(self):
       return self.__str__()

