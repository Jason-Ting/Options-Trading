#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 14:17:41 2021

@author: jasonting
change
"""


#Imports require Yahoo_Fin Instaleld [Python Package] pip install yahoo-fin
import yahoo_fin.stock_info as si 
from yahoo_fin.options import *
from datetime import date




class Options:
    """Define Class Options"""

    def __init__(self, ticker, rf, exp_date = None):
        """Initialize Constructor with attributes. Init takes stock ticker in string format,
        1-Month [T-Bill] Risk Free Rate, Expiration Date of Options(Initializes to closest date
        if none)--String."""
        
        #Input Attributes
        self.ticker = ticker
        self.rf = rf/100
        self.exp_date = exp_date
       
        
        #Stock Attributes   
        self.price_underlying = round(si.get_live_price(ticker),2) # Spot Price
        self.div = si.get_dividends(ticker) # Dividend Yield
        
        #Contract Chain
        self.calls = get_calls(ticker,exp_date) #Get Call Chain
        self.puts = get_puts(ticker,exp_date) #Get Put Chain
      
        #Contract's Attributes In Columns[Contract Name,Implied Volatility,Strike]
        self.call_name = self.calls['Contract Name'] #Contracts' Names
        self.put_name = self.calls['Contract Name']
        self.vega_calls = self.calls['Implied Volatility'] #Implied Volatility
        self.vega_puts = self.puts['Implied Volatility'] 
        self.call_k = self.calls['Strike'] #Strikes
        self.puts_k = self.puts['Strike']
        
        #Initialize Call & Put Up/Downstates to be used for Binomial Tree
        self.Cu = 0 
        self.Cd = 0
        self.Pu = 0 
        self.Pd = 0
    
   
        #Date Attributes
        if exp_date != None: #If expiration date is specified, determine exponent for rf
            
            today_date = date.today() #Create dateobject for today's date
            exp_date_lc = exp_date.split('/')
            
            y = int(exp_date_lc[-1])
            m = int(exp_date_lc[0])
            d = int(exp_date_lc[1])
        
            exp_date_object= datetime.date(y,m,d) #Create 2nd dateobject for expiration
        
            #Determine months between contracts' expiration & today's date
            self.num_months = (exp_date_object.year - today_date.year) * 12 + (exp_date_object.month - today_date.month)
            
        else: #Else set exponent = 0 
            self.num_months = 0 
       
        
    #Repr Method 
    def __repr__(self):
        """Repr Method returns String with Call Contract Chain & Put Contract Chain"""
        s = ''
        s+= 'Calls' + str(self.calls) 
        s+= ('\n')
        s+='Puts' + str(self.puts)
        return s 
    
    
    #Method 1 
    def pc_parity_arbitrage(self):
        lc = []
        
        for c in range(len(self.call_k)):
            for p in range(len(self.puts_k)):
                if self.call_k[c] == self.puts_k[p]: #If 2 equal strikes are found, append indicies to list of list
                    lc += [[c,p]] #List of Lists formmated as [Call Index, Put Index]
        
        #print(lc) Uncomment lc and run for furthur clarification on output
        
        for n in range(len(lc)):
            call_index = lc[n][0]
            put_index = lc[n][1]
     
            c_contract = self.calls[call_index: call_index + 1] 
            c_contract_name = c_contract['Contract Name'] #Get Contract Name
            c_name = c_contract_name[call_index] #Splice by Call Index
            c_contract_bid = round(c_contract['Bid'],2) #Current ask price of current iteration of call contract 
            c_contract_ask = round(c_contract['Ask'],2)
         
            c_contract_strike =c_contract['Strike'] #Determine strike of contract
            #print(c_contract_strike)
            pv_k = (c_contract_strike[call_index])/(1+self.rf)**self.num_months #Determine Present Value of strike
            #print('present value of k',pv_k)
            pv_div = (self.div)/(1+self.rf) ** self.num_months
        
         
            p_contract = self.puts[put_index :put_index + 1]
            p_contract_ask = round(p_contract['Ask'],2) #Current ask price of current iteration of put contract
            p_contract_bid = round(p_contract['Bid'],2)
        
     
            #If Conversion > 0: Make Arbitrage Free Profit| Syntehtic :[Long Put, Short Call], Long Underlying
            conversion = round(c_contract_bid[call_index] - p_contract_ask[put_index] - self.price_underlying + pv_k,3) #c_contract_strike[call_index],2) # Calculate Conversion
            
        
            reversal = round(c_contract_ask[call_index] - p_contract_bid[put_index] - self.price_underlying + pv_k,3) #c_contract_strike[call_index],2)  #Calculate Reversal
    
            print(str(n)+'.', 'Contract:'+str(c_name) +'|','Conversion:', str(conversion) +'|'+' Reversal:', reversal, end = ' ')
        
            if conversion > 0:
                print('\n')
                print('      Conversion Found')
                print("      Synthetic Portfolio: Buy Underlying:$"+ str(self.price_underlying)+' |', "Buy Put:$"+ str(p_contract_ask[put_index])+' |', "Sell Call:$"+str(c_contract_bid[call_index]))
                profit = (pv_k - self.price_underlying + c_contract_bid[call_index] - p_contract_ask[put_index]) * 100
                print('      Payoff from Synthetic Portfolio:$'  + '%.2f' % profit)
                print('      Strike',pv_k,'Call Bid',c_contract_bid[call_index],'Put Ask',p_contract_ask[put_index])
         
            if reversal < 0:
                print('\n')
                print('     Reversal Found')
                print("     Synthetic Portfolio: Buy Call:$"+str(c_contract_ask[call_index])+' |', "Sell Put:$"+str(p_contract_bid[put_index])+' |', "Sell Underlying:$"+str(self.price_underlying))
                profit = (self.price_underlying - pv_k + p_contract_bid[put_index] - c_contract_ask[call_index]) * 100
                print('     Payoff from Synthetic Portfolio:$ '+'%.2f' % profit)
                print('     Strike',pv_k,'Call Ask',c_contract_ask[call_index],'Put Bid',p_contract_bid[put_index])
     
            print('\n')
            
        

    #Method 2 
    def risk_neutral(self):
        """Method uses risk-neutral probabilities to determine the price of an option, 
        within 1 Period. Inputs: Estimated upstate & downstate in % | 
        Output: Option price."""
       
        
        print("Enter Upstate, Downstate, Strike")   
        upstate, downstate, strike = [float(x) for x in input().split(',')] 
        
        print("Enter Contract Type [C for Call, P for Put] ")
        option_type = input()
        #input('Upstate %: ' ,upstate , 'Downstate %: ', Downstate, 'Strike', Strike, 'Put or Call', Option)
        
        Su = self.price_underlying *(1+(upstate/100)) #Price of stock in upstate
        Sd = self.price_underlying *(1-(downstate/100)) #Price of stock in downstate
        
        
        p = (self.price_underlying*(1+self.rf) - Sd)/(Su - Sd)
        
        if option_type == 'C' or option_type == 'c':
            
            #Determine Payoffs of Calls 
            self.Cu = max(Su - strike, 0)
            self.Cd = max(Sd - strike, 0)
            
            option_price = (p * self.Cu) + (1-p)*self.Cd/(1+self.rf)
            
        if option_type == 'P' or option_type == 'p':
           
            #Determine Payoff of Puts
            self.Pu = max(strike - Su,0)
            self.Pd = max(strike - Sd,0)
        
            option_price = (p * self.Pu) + (1-p)*self.Pd/(1+self.rf)
        
        print('Risk Neutral Probabilities:'+ str(round(p,2)) +' Upstate | ' +str(round(1-p,2))+' For Downstate')
        print('Estimated Option Price: $' + str(round(option_price,2)))
        
        
        

    #Method 3 
    def delta_hedge_portfolio(self):
        """Method computes the intial values of stocks and bonds @ rf to create
        the replicating or a zero delta portfolio. Portfolio is self-financing"""
        
        print("Enter Upstate, Downstate, Strike")   
        upstate, downstate, strike = [float(x) for x in input().split(',')] 
        
        print("Enter Contract Type [C for Call, P for Put] ")
        option_type = input()
        
        Su = self.price_underlying *(1+(upstate/100)) #Price of stock in upstate
        Sd = self.price_underlying *(1-(downstate/100)) #Price of stock in downstate
        
        if option_type == 'C' or option_type == 'c':
            
            self.Cu = max(Su - strike, 0)
            self.Cd = max(Sd - strike, 0)
            
            delta = (self.Cu - self.Cd)/(Su-Sd)
            bond = (self.Cd-Sd * delta)/(1+self.rf)
            cost_of_trade = delta * self.price_underlying + bond 
        
            if delta > 0:
                print("Long ", delta, "shares")
                
            elif delta <= 0: 
                print("Short ", delta, "shares")
            
            if bond <= 0: 
                print("Borrow $", -bond)
            
            elif bond > 0: 
                print("Lend $", bond)
                
                
            print('Initial Replicating Portfolio: Total Cost of Trade $', round(cost_of_trade,2))
            
            
        if option_type == 'P' or option_type == 'c':
            
            self.Pu = max(strike - Su,0)
            self.Pd = max(strike - Sd,0)
        
            delta = (self.Pu - self.Pd)/(Su-Sd)
            bond = (self.Pd-Sd * delta)/(1+self.rf)
            cost_of_trade = delta * self.price_underlying + bond 
            
            
            if delta > 0:
                print("Long ", delta, "shares")
                
            elif delta <= 0: 
                print("Short ", delta, "shares")
            
            if bond <= 0: 
                print("Borrow $", -bond)
            
            elif bond > 0: 
                print("Lend $", bond)
                
                
            print('Initial Replicating Portfolio: Total Cost of Trade $', round(cost_of_trade,2))
            
            
        
            
            
            
           
        
        
# Test Code         
if __name__ == "__main__":
    x = Options('^XSP',0.06)
    x.pc_parity_arbitrage()
    x.risk_neutral()
    x.delta_hedge_portfolio()
 
    
         
     