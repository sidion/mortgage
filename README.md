# mortgage calculator

Create a mortgage calculator API using any language/tech stack. The API should accept and
return JSON.

# GET /payment-amount
Get the recurring payment amount of a mortgage
Params:
Asking Price
Down Payment*
Payment schedule***
Amortization Period**
Return:
Payment amount per scheduled payment

# GET /mortgage-amount
Get the maximum mortgage amount
Params:
payment amount
Down Payment(optional)****
Payment schedule***
Amortization Period**
Return:
Maximum Mortgage that can be taken out

# PATCH /interest-rate
Change the interest rate used by the application
Params:
Interest Rate
Return:
message indicating the old and new interest rate

# Description
* Must be at least 5% of first $500k plus 10% of any amount above $500k (So $50k on a $750k
mortgage)
* Min 5 years, max 25 years
* Weekly, biweekly, monthly
* If included its value should be added to the maximum mortgage returned
* Mortgage interest rate 2.5% per year

# Mortgage insurance 
Mortgage insurance is required on all mortgages with less than 20% down. Insurance must be
calculated and added to the mortgage principal. Mortgage insurance is not available for
mortgages > $1 million.

Mortgage insurance rates are as follows:
Down payment Insurance Cost
5-9.99% 3.15%
10-14.99% 2.4%
15%-19.99% 1.8%
20%+ N/A
Payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
P = Payment
L = Loan Principal
c = Interest Rate
