import resend

resend.api_key =  "re_hNSyVFyr_HcRCgvS6HtEZ2BS2u1RSQimJ"

params: resend.Domains.CreateParams = {
  "name": "tcc.cognitive.com",
  "custom_return_path": "outbound"
}

resend.Domains.create(params)