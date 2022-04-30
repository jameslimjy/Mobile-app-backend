from twilio.rest import Client

# Twilio Account SID and Auth Token
client = Client("AC9c4aaa5a9b8b4e252a9a0d94ca76753c", "fefff5db6c1f01c72698e9718b399beb")
twilio_number = "+15039266081"

def send_phone_otp(to_num, otp):
    ''' 
    Takes in an phone number and OTP and sends an sms to the phone number containing the OTP
    '''
    client.messages.create(to = to_num, 
                        from_ = twilio_number, 
                        body = f"[iTown2@SG] Your SMS OTP is {otp}. It will expire after 2 minutes.")
