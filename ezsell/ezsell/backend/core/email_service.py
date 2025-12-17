# Email service for sending verification codes
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from datetime import datetime, timedelta
from core.config import settings

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    async def send_verification_email(to_email: str, code: str) -> bool:
        """
        Send verification code email
        Returns True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "EZSell - Email Verification Code"
            message["From"] = f"EZSell <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            
            # Email content
            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                  <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #8b5cf6; margin: 0;">EZSell</h1>
                    <p style="color: #6b7280; margin-top: 10px;">Email Verification</p>
                  </div>
                  
                  <h2 style="color: #1f2937; margin-bottom: 20px;">Verify Your Email</h2>
                  
                  <p style="color: #4b5563; line-height: 1.6; margin-bottom: 25px;">
                    Thank you for signing up with EZSell! Please use the following verification code to complete your registration:
                  </p>
                  
                  <div style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
                    <span style="color: white; font-size: 32px; font-weight: bold; letter-spacing: 8px;">{code}</span>
                  </div>
                  
                  <p style="color: #4b5563; line-height: 1.6; margin-bottom: 15px;">
                    This code will expire in <strong>2 minutes</strong>.
                  </p>
                  
                  <p style="color: #6b7280; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    If you didn't request this code, please ignore this email.
                  </p>
                  
                  <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #6b7280; font-size: 12px; margin: 5px 0;">
                      © 2025 EZSell - Your Trusted Marketplace
                    </p>
                    <p style="color: #6b7280; font-size: 12px; margin: 5px 0;">
                      Buy & Sell Mobile Phones, Laptops, and Furniture
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            text_content = f"""
            EZSell - Email Verification
            
            Thank you for signing up with EZSell!
            
            Your verification code is: {code}
            
            This code will expire in 2 minutes.
            
            If you didn't request this code, please ignore this email.
            
            © 2025 EZSell - Your Trusted Marketplace
            Buy & Sell Mobile Phones, Laptops, and Furniture
            """
            
            # Attach both HTML and plain text versions
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email using Gmail SMTP with timeout
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
                timeout=30,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending verification email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    async def send_password_reset_email(to_email: str, code: str) -> bool:
        """
        Send password reset code email
        Returns True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "EZSell - Password Reset Code"
            message["From"] = f"EZSell <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            
            # Email content
            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                  <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #8b5cf6; margin: 0;">EZSell</h1>
                    <p style="color: #6b7280; margin-top: 10px;">Password Reset Request</p>
                  </div>
                  
                  <h2 style="color: #1f2937; margin-bottom: 20px;">Reset Your Password</h2>
                  
                  <p style="color: #4b5563; line-height: 1.6; margin-bottom: 25px;">
                    We received a request to reset your password. Please use the following code to reset your password:
                  </p>
                  
                  <div style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
                    <span style="color: white; font-size: 32px; font-weight: bold; letter-spacing: 8px;">{code}</span>
                  </div>
                  
                  <p style="color: #4b5563; line-height: 1.6; margin-bottom: 15px;">
                    This code will expire in <strong>1 minute</strong>.
                  </p>
                  
                  <p style="color: #dc2626; line-height: 1.6; margin-top: 20px; padding: 15px; background-color: #fef2f2; border-left: 4px solid #dc2626; border-radius: 4px;">
                    <strong>Security Notice:</strong> If you didn't request a password reset, please ignore this email and ensure your account is secure.
                  </p>
                  
                  <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #6b7280; font-size: 12px; margin: 5px 0;">
                      © 2025 EZSell - Your Trusted Marketplace
                    </p>
                    <p style="color: #6b7280; font-size: 12px; margin: 5px 0;">
                      Buy & Sell Mobile Phones, Laptops, and Furniture
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            text_content = f"""
            EZSell - Password Reset Request
            
            We received a request to reset your password.
            
            Your password reset code is: {code}
            
            This code will expire in 1 minute.
            
            Security Notice: If you didn't request a password reset, please ignore this email and ensure your account is secure.
            
            © 2025 EZSell - Your Trusted Marketplace
            Buy & Sell Mobile Phones, Laptops, and Furniture
            """
            
            # Attach both HTML and plain text versions
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email using Gmail SMTP with timeout
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
                timeout=30,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            import traceback
            traceback.print_exc()
            return False

email_service = EmailService()
