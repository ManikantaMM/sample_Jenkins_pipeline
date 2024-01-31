import boto3
import argparse
import sys
import os
from datetime import datetime
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Function to retrieve AMIs in a specific region and between specified dates
def amis_in_region(session,hostname,region_name,from_date_to_check,to_date_to_check):
    try:
        if (hostname!=None or hostname!="None")and (region_name==None or region_name=="None":
            regionCode = hostname.split("-")[0]
            region_name = region_from_hostname(regionCode)

        ec2_client = session.client('ec2', region_name)
        tag_key = 'Name'
        filtered_amis = []

        #if user gave the hostname then it will get the details of the particular host
        if (hostname!=None or hostname!="None"):
            filters=[
                {'Name':f'tag:{tag_key}','Values':[hostname]}
            ]
            response = ec2_client.describe_images(Filters=filters)
            if response['Images']:
                image=response['Images'][0]
                ami_id=image['ImageId']
                creation_date=datetime.strptime(image['CreationDate'],'%Y-%m-%dT%H:%M:%S.%fZ')
                if creation_date>=from_date_to_check and creation_date<=to_date_to_check:
                    filtered_amis.append({
                        'Host_Name':hostname,
                        'AMI_ID': ami_id,
                        'Creation_Date':creation_date
                    })
                    print(f"{hostname} details added in the list")
                else:
                    print(f"{hostname} details not added in the list and the list is empty")
                    print(f"because the {hostname} with the ami id {ami_id} is not in the given range{creation_date} ")
        #to get all amis details in one region
        else:

            response = ec2_client.describe_images()
            for image in response['Images']:
                creation_date = datetime.strptime(image['CreationDate'],'%Y-%m-%dT%H:%M:%S.%fZ')
                if tag_key in [tag['Key'] for tag in image.get('Tags',[])] and creation_date > from_date_to_check and creation_date < to_date_to_check:
                    for tag in image['Tags']:
                        if tag['Key'] == tag_key and hostname==None:
                            filtered_amis.append({
                                'Host_Name': tag['Value'],
                                'AMI_ID': image['ImageId'],
                                'Creation_Date': creation_date
                            })
                            print(f"-----{tag['Value']} {image['ImageId']} {creation_date}")
            print(f"amis in the {region_name} are added in the list")

        return filtered_amis
    except Exception as e:
        print(f"Error in amis_in_region : {e} ")
        sys.exit(1)


# Function to retrieve available AWS regions
def get_available_regions(session):
    try:
        ec2_client = session.client('ec2')
        regions = ec2_client.describe_regions()
        available_regions = [region['RegionName'] for region in regions['Regions']]
        return available_regions
    except Exception as e:
        print(f"Error retrieving available regions: {e}")
        return []

# Function to map region codes to region names
def region_from_hostname(regionName):
    try:
        switch = {
            "pdx": "us-west-2",
            "hkg": "ap-east-1",
            "cpt": "af-south-1",
            "bom": "ap-south-1",
            "syd": "ap-southeast-2",
            "sin": "ap-southeast-1",
            "fra": "eu-central-1",
            "lon": "eu-west-2",
            "gru": "sa-east-1",
        }
        return switch.get(regionName, "None Found")
    except Exception as e:
        print(f"Error occurred in region_from_hostname : {e} ")

# Function to convert string dates to datetime objects and validate dates
def parse_and_validate_dates(start_date_str,end_date_str):
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date=datetime.strptime(end_date_str, "%Y-%m-%d")
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")

        return [start_date, end_date]
    except Exception as e:
        if e == ValueError:
            print("Please provide dates in the format YYYY-MM-DD")
        else:
            print(f" Error in convert_str_to_date : {e}")
        sys.exit(1)

# Function to save AMI details to a CSV file
def save_to_csv(amis,filename):
    try:
        file_name = filename+".csv"
        file_path = os.path.abspath(file_name)
        if os.path.exists(file_path):
            print(f'file {file_name} already exists')
            os.remove(file_path)
    
        with open(file_name, mode='w', newline='') as csvfile:
            fieldnames = ['Host_Name', 'AMI_ID', 'CreationDate']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for ami in amis:
                writer.writerow({
                    'Host_Name': ami['Host_Name'],
                    'AMI_ID': ami['AMI_ID'],
                    'CreationDate': ami['Creation_Date']
                })
        print("Output saved to ",file_name)

    except Exception as e:
        print(f"Error in {file_name} : {e}")
    return file_path


# Function to send an email with an attachment
def send_email(subject, body, to_email, attachment_path = None):
    try:
        # SMTP email configuration
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        sender_email = 'manikantam9116@gmail.com'
        sender_password = 'fpqryunhiovbvlky'        #'fpqryunhiovbvlky'


        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        msg.attach(MIMEText(body,'plain'))

        if attachment_path:
            filename = attachment_path.split('/')[-1]
            attachment = open(attachment_path, "rb")

            # Add file as application/octet-stream
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {filename}')
            msg.attach(part)
            # Create a secure SSL context
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)

            # Send the message via the server.
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            print("Email sent successfully!")
    except Exception as e:
            print(f"An error occurred in send_email: {e}")




def main():
    try:
        # to pass the script arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("host_name",nargs="?", help="Provide AWS Instance Name")
        parser.add_argument("region_name",nargs="?", help="Please provide AWS region name")
        parser.add_argument("Start_Date",nargs="?",help="Start date")
        parser.add_argument("End_Date",nargs="?",help="End date")

        args = parser.parse_args()

        if not (args.End_Date and args.Start_Date):
            print("Start date and End date are mandatory")
            sys.exit(1)

        hostname = args.host_name
        region_name = args.region_name
        dates = parse_and_validate_dates(args.Start_Date, args.End_Date)
        start_date = dates[0]
        end_date = dates[1]

        session = boto3.Session(profile_name="appd-aws-650959535457-dev-650959535457")

        amis_list = []

        #check region name an hostname
        if region_name != None or hostname != None:
            amis_list = amis_in_region(session,hostname, region_name, start_date, end_date)
        elif (hostname == None and region_name == None):
            regions = get_available_regions(session)
            for region in regions:
                amis_in_this_region = amis_in_region(session,hostname, region, start_date, end_date)
                amis_list.extend(amis_in_this_region)
        else:
            print("Usage : python amis_in_between_specified_dates.py <--host_name(optional)> <--region_name(optional)> <start_date> <end_date>")
            sys.exit(1)

        # to name the file base don the input
        filename = "all_amis"
        if (hostname != None):
            filename=hostname
        elif (region_name!=None):
            filename=region_name



        file_path = save_to_csv(amis_list,filename)

        email_subject = f'{filename}'
        email_body = f'PFA of {filename}'
        recipient_mail = "manikantam9117@gmail.com"
        send_email(email_subject, email_body, recipient_mail, file_path)
        os.remove(file_path)
    except Exception as e:
        print(f"Error occurred in main : {e}")



if __name__=='__main__':
    main()
