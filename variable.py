'''
Created on Aug 27, 2018

@author: Xuan Lin

Define all the error messages, JSON object key words and const values
'''

var_mortgage_rate = 'mortgage_rate'
var_old_rate = 'old_rate'
var_new_rate = 'new_rate'
var_response_msg = 'message'
var_response_success = 'successful'
var_reponse_fail = 'failed'
var_result = 'result'
var_payment_amount = 'payment_amount'
var_payment_schdule = 'payment_schedule'

var_asking_price = 'asking_price'
var_down_payment = 'down_payment'
var_payment_schedule = 'payment_schedule'
var_amortization_period = 'amortization_period'

var_maximum_mortgage = 'maximum_mortgage'

err_invalid_json = 'Invalid JSON input'
err_invalid_input_rate = 'Invalid JSON input, please use following template {{\'{0}\': 0.xxx}}'.format(var_mortgage_rate)
err_invalid_mortgage_rate = 'Invalid mortgage rate'
err_invalid_parameters = 'There is at least one parameter is missing here'
err_invalid_amortization_period = "Invalid amortization period"
err_invalid_asking_price = "Invalid asking price"
err_invalid_down_payment = "Invalid down payment"
err_invalid_payment_amount = "Invalid payment amount"
err_invalid_payment_schedule = "Invalid payment schedule"
err_not_enough_down_payment = "The down payment is not enough"
err_no_mortgage_insurance_option = 'Mortgage insurance is not available for mortgages > $1 million.'

#Mortgage interest rate 2.5% per year
mortgage_rate_per_year = 0.025

const_five_years = 5
const_twenty_five_years = 25

const_500k_threshold = 500*1000
const_one_million = 1000000

const_first_500k_percent = 0.05
const_after_500k_percent = 0.1

const_insurance_required_down_percent = 0.2
const_insurance_rate_level_1 = 0.0315
const_insurance_rate_level_2 = 0.024
const_insurance_rate_level_3 = 0.018

#assume one year has 12 months / 52 weeks
dict_payment_schedule = {'weekly': 52, 'biweekly': 27, 'monthly': 12}
