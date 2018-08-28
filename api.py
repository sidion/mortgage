'''
Created on Aug 27, 2018

@author: Xuan Lin
'''
from __future__ import division

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask import jsonify
from flask import request

import sys
import urllib
import json
import logging

import variable

app = Flask(__name__)
auth = HTTPBasicAuth()

#Flask Logging to Stdout
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)

#hard coded user name and password for testing purpose
users = {
    "admin": "mortgage",
    "dev": "testpw"
}

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

@app.route('/payment-amount', methods=['GET']) #allows only GET
def get_payment():
    '''
    GET /payment-amount
    Get the recurring payment amount of a mortgage
    
    Params:
    Asking Price
    Down Payment*
    Payment schedule***
    Amortization Period** This is alwasya integer between 5 to 25
    
    The input parameter will be passed as a json in the querying string. For instance,
    127.0.0.1:5000/payment-amount?json={...}
    The JSON will be passed in URL encoding
    
    {"asking_price": 650000,"down_payment": 100000,"payment_schedule": "monthly","amortization_period": 10}
    to
    %7B%27asking_price%27%3A+650000%2C%27down_payment%27%3A+100000%2C%27payment_schedule%27%3A+%27monthly%27%2C%27amortization_period%27%3A+10%7D
    
    Return:
    Payment amount per scheduled payment
    '''
    json_str = request.args.get('json', default = '', type = str) #if ther is no key named json then return empty string
    
    if len(json_str) == 0:
        return jsonify({variable.var_result : variable.var_reponse_fail,
            variable.var_response_msg : variable.err_invalid_json}) 
    else :
        try:
            json_url_decode = urllib.unquote(json_str)
            app.logger.info(json_url_decode)
            
            json_object = json.loads(json_url_decode)
            
            #check if all the required parameters are here
            missing_param = False;
            
            if variable.var_asking_price not in json_object:
                missing_param = True
            if variable.var_down_payment not in json_object:
                missing_param = True
            if variable.var_payment_schedule not in json_object:
                missing_param = True
            if variable.var_amortization_period not in json_object:
                missing_param = True
            
            if missing_param == True:
                return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_parameters}) 

            if json_object[variable.var_payment_schdule] not in variable.dict_payment_schedule:
                return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_payment_schedule}) 
            
            #Min 5 years, max 25 years            
            if type(json_object[variable.var_amortization_period]) is int:
                if json_object[variable.var_amortization_period] < variable. const_five_years or \
                    json_object[variable.var_amortization_period] > variable.const_twenty_five_years :
                    return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_amortization_period}) 
            else :
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_invalid_amortization_period}) 
            
            '''
            The minimal down payment must be at least 5% of first $500k plus 10% of any amount above 
            $500k (So $50k on a $750k mortgage)
            '''
            minimal_down_payment = 0
            
            if type(json_object[variable.var_asking_price]) is not int and \
                type(json_object[variable.var_asking_price]) is not float :
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_invalid_asking_price})
            
            if type(json_object[variable.var_down_payment]) is not int and \
                type(json_object[variable.var_down_payment]) is not float :
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_invalid_down_payment})
            
            if json_object[variable.var_asking_price] > variable.const_500k_threshold:
                minimal_down_payment = (json_object[variable.var_asking_price] - variable.const_500k_threshold) * variable.const_after_500k_percent + \
                    variable.const_500k_threshold * variable.const_first_500k_percent
            else :
                minimal_down_payment = json_object[variable.var_asking_price] * variable.const_first_500k_percent

            if json_object[variable.var_down_payment] < minimal_down_payment :
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_not_enough_down_payment})
            
            #calculate the loan principal and the additional insurance cost
            loan_principal = json_object[variable.var_asking_price] - json_object[variable.var_down_payment]
            down_payment_rate = json_object[variable.var_down_payment] / json_object[variable.var_asking_price]
            
            app.logger.info("down_payment_rate: {0}, loan_principal: {1}".format(down_payment_rate, loan_principal))
            
            '''
            Mortgage insurance is required on all mortgages with less than 20% down. Insurance must be
            calculated and added to the mortgage principal. Mortgage insurance is not available for
            mortgages > $1 million.
            '''
            if loan_principal > variable.const_one_million and down_payment_rate < variable.const_insurance_required_down_percent:
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_no_mortgage_insurance_option})
            
            '''
            Mortgage insurance rates are as follows:
            Down payment Insurance Cost
            5-9.99% 3.15%
            10-14.99% 2.4%
            15%-19.99% 1.8%
            20%+ N/A
            '''
            if down_payment_rate < variable.const_insurance_required_down_percent:
                if down_payment_rate >= 0.05 and down_payment_rate < 0.1 :
                    loan_principal += loan_principal*variable.const_insurance_rate_level_1
                elif down_payment_rate >= 0.1 and down_payment_rate < 0.15 :
                    loan_principal += loan_principal*variable.const_insurance_rate_level_2
                elif down_payment_rate >= 0.15 and down_payment_rate < 0.2 :
                    loan_principal += loan_principal*variable.const_insurance_rate_level_3
            
            '''
            Payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
            P = Payment
            L = Loan Principal
            c = Interest Rate
            '''
            c = variable.mortgage_rate_per_year / variable.dict_payment_schedule[json_object[variable.var_payment_schdule]]
            n = json_object[variable.var_amortization_period]*variable.dict_payment_schedule[json_object[variable.var_payment_schdule]]
            
            payment = loan_principal*(c * (1+c)**n) / ((1+c)**n-1)
            payment = round(payment,2)  #round to 2 decimal places
            
            json_data = {}
            json_data[variable.var_payment_schdule] = json_object[variable.var_payment_schdule]
            json_data[variable.var_payment_amount] = payment
            
            return jsonify({variable.var_result : variable.var_response_success,
                                variable.var_response_msg : json_data})
        except ValueError, e:
            app.logger.error(e)
            return jsonify({variable.var_result : variable.var_reponse_fail,
                                variable.var_response_msg : variable.err_invalid_json}) 

@app.route('/mortgage-amount', methods=['GET']) #allows only GET
def get_mortgage():
    '''GET /mortgage-amount
    Get the maximum mortgage amount
    
    Params:
    payment amount
    Down Payment(optional)**** If included its value should be added to the maximum mortgage returned
    Payment schedule***
    Amortization Period** This is a number between 5 and 25
    
    input JSON object:
    {"payment_amount": 5278.17,"down_payment": 100000,"payment_schedule": "monthly","amortization_period": 10}
    
    After URL encoding:
    %7B%22payment_amount%22%3A+5278.17%2C%22down_payment%22%3A+100000%2C%22payment_schedule%22%3A+%22monthly%22%2C%22amortization_period%22%3A+10%7D
    
    Return:
    Maximum Mortgage that can be taken out (Include the down payment and exclude mortgage insurance if needed)
    '''
    json_str = request.args.get('json', default = '', type = str)
    
    if len(json_str) == 0:
        return jsonify({variable.var_result : variable.var_reponse_fail,
            variable.var_response_msg : variable.err_invalid_json}) 
    else :
        try:
            json_url_decode = urllib.unquote(json_str)
            app.logger.info(json_url_decode)
            
            json_object = json.loads(json_url_decode)
            
            #check if all the required parameters are here
            missing_param = False;
            
            if variable.var_payment_amount not in json_object:
                missing_param = True
            if variable.var_payment_schedule not in json_object:
                missing_param = True
            if variable.var_amortization_period not in json_object:
                missing_param = True
            
            if missing_param == True:
                return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_parameters})
            
            #The payment need to be a number
            if type(json_object[variable.var_payment_amount]) is not int and \
                type(json_object[variable.var_payment_amount]) is not float :
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_invalid_payment_amount})
            
            # The payment schedule should one of following: weekly, biweekly, monthly
            if json_object[variable.var_payment_schdule] not in variable.dict_payment_schedule:
                return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_payment_schedule}) 
            
            #Min 5 years, max 25 years            
            if type(json_object[variable.var_amortization_period]) is int:
                if json_object[variable.var_amortization_period] < variable. const_five_years or \
                    json_object[variable.var_amortization_period] > variable.const_twenty_five_years :
                    return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_amortization_period}) 
            else :
                return jsonify({variable.var_result : variable.var_reponse_fail,
                    variable.var_response_msg : variable.err_invalid_amortization_period})
            
            down_payment = 0
            
            if variable.var_down_payment in json_object:
                #The down payment need to be a number too
                if type(json_object[variable.var_down_payment]) is not int and \
                    type(json_object[variable.var_down_payment]) is not float :
                    return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_down_payment})
                else :
                    down_payment = json_object[variable.var_down_payment]
            else :
                #if there is no down payment here, we always assume the down payment is minimal required amount
                pass
                
            ''' 
            Formula:
            L = P / {[c(1 + c)^n]/[(1 + c)^n - 1]}
            '''
            c = variable.mortgage_rate_per_year / variable.dict_payment_schedule[json_object[variable.var_payment_schdule]]
            n = json_object[variable.var_amortization_period]*variable.dict_payment_schedule[json_object[variable.var_payment_schdule]]   
            
            loan_principal = json_object[variable.var_payment_amount] / ((c * (1+c)**n) / ((1+c)**n-1))
            
            if down_payment > 0:
                down_payment_rate = down_payment / loan_principal
                
                #deduct the mortgage insurance
                if down_payment_rate >= 0.05 and down_payment_rate < 0.1 :
                    loan_principal = loan_principal * (1-variable.const_insurance_rate_level_1)
                elif down_payment_rate >= 0.1 and down_payment_rate < 0.15 :
                    loan_principal = loan_principal * (1-variable.const_insurance_rate_level_2)
                elif down_payment_rate >= 0.15 and down_payment_rate < 0.2 :
                    loan_principal = loan_principal * (1-variable.const_insurance_rate_level_3)
            else :
                #deduct the mortgage insurance with highest rate
                loan_principal = loan_principal * (1-variable.const_insurance_rate_level_1)
                
                if loan_principal > variable.const_500k_threshold:
                    down_payment = (loan_principal - variable.const_500k_threshold) * variable.const_after_500k_percent + \
                        variable.const_500k_threshold * variable.const_first_500k_percent
                else :
                    down_payment = loan_principal * variable.const_first_500k_percent
                
                app.logger.info("Calculated minimal down payment: {0}".format(down_payment))
            
            loan_principal += down_payment
            loan_principal = round(loan_principal,2)  #round to 2 decimal places
            
            json_data = {}
            json_data[variable.var_maximum_mortgage] = loan_principal
            
            return jsonify({variable.var_result : variable.var_response_success,
                                variable.var_response_msg : json_data})
        except ValueError, e:
            print e
            return jsonify({variable.var_result : variable.var_reponse_fail,
                                variable.var_response_msg : variable.err_invalid_json})
            

@app.route('/interest-rate', methods=['PATCH']) #allows only PUT
@auth.login_required    #do a simple authentication to limit within system admin group to modify the rate
def change_rate():
    '''
    PATCH /interest-rate
    Change the interest rate used by the application
    
    Params:
    Interest Rate per year
    
    Return:
    message indicating the old and new interest rate
    '''
    if request.is_json: 
        content = request.get_json(silent=True) #mark silent is True to return None instead of throw exception when validation failed
        
        if content != None:
            app.logger.info(content)
            
            # First make sure there is a key named mortgage_rate and then check its value to see if that can be a rate
            if variable.var_mortgage_rate in content :
                if type(content[variable.var_mortgage_rate]) is float:
                    if content[variable.var_mortgage_rate] <= 0 or content[variable.var_mortgage_rate] >=1.0:
                        return jsonify({variable.var_result : variable.var_reponse_fail,
                            variable.var_response_msg : variable.err_invalid_mortgage_rate})
                else :
                    return jsonify({variable.var_result : variable.var_reponse_fail,
                        variable.var_response_msg : variable.err_invalid_mortgage_rate})
                
                json_data = {}  #build the response JSON object
                
                json_data[variable.var_old_rate] = variable.mortgage_rate_per_year
                variable.mortgage_rate_per_year = content[variable.var_mortgage_rate]
                json_data[variable.var_new_rate] = variable.mortgage_rate_per_year
                
                app.logger.info("user: {0} changed the mortgage rate to {1}".format(auth.username(), variable.mortgage_rate_per_year))
                
                return jsonify({variable.var_result : variable.var_response_success,
                                variable.var_response_msg : json_data})
    
    return jsonify({variable.var_result : variable.var_reponse_fail,
            variable.var_response_msg : variable.err_invalid_json})


if __name__ == '__main__':
    app.run()
