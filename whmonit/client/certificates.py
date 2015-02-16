#!/usr/bin/env python
# -*- coding: utf-8 -*-

# *.monitowl.com
MONITOWL_WEB_CRT = """-----BEGIN CERTIFICATE-----
MIIDDDCCAfSgAwIBAgIDAQAgMA0GCSqGSIb3DQEBBQUAMD4xCzAJBgNVBAYTAlBM
MRswGQYDVQQKExJVbml6ZXRvIFNwLiB6IG8uby4xEjAQBgNVBAMTCUNlcnR1bSBD
QTAeFw0wMjA2MTExMDQ2MzlaFw0yNzA2MTExMDQ2MzlaMD4xCzAJBgNVBAYTAlBM
MRswGQYDVQQKExJVbml6ZXRvIFNwLiB6IG8uby4xEjAQBgNVBAMTCUNlcnR1bSBD
QTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAM6xwS7TT3zNJc4YPk/E
jG+AanPIW1H4m9LcuwBcsaD8dQPugfCI7iNS6eYVM42sLQnFdvkrOYCJ5JdLkKWo
ePhzQ3ukYbDYWMzhbGZ+nPMJXlVjhNWo7/OxLjBos8Q82KxujZlakE403Daaj4GI
ULdtlkIJ89eVgw1BS7Bqa/j8D35in2fE7SZfECYPCE/wpFcozo+47UX2bu4lXapu
Ob7kky/ZR6By6/qmW6/KUz/iDsaWVhFu9+lmqSbYf5VT7QqFiLpPKaVCjF62/IUg
AKpoC6EahQGcxEZjgoi2IrHu/qpGWX7PNSzVttpd90gzFFS269lvzs2I1qsb2pY7
HVkCAwEAAaMTMBEwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEA
uI3O7+cUus/usESSbLQ5PqKEbq24IXfS1HeCh+YgQYHu4vgRt2PRFze+GXYkHAQa
TOs9qmdvLdTN/mUxcMUbpgIKumB7bVjCmkn+YzILa+M6wKyrO7Do0wlRjBCDxjTg
xSvgGrZgFCdsMneMvLJymM/NzD+5yCRCFNZX/OYmQ6kd5YCQzgNUKD73P9P4Te1q
CjqTE5s7FCMTY5w/0YcneeVMUeMBrYVdGjux1XMQpNPyvG5k9VpWkKjHDkx0Dy5x
O/fIR/RpbxXyEV6DHpx8Uq79AtoSqFlnGNu8cN2bsWntgM6JQEhqDjXKKWYVIZQs
6GAqm4VKQPNriiTsBhYscw==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIEuTCCA6GgAwIBAgIRAMU8GL+PP5zHcwapxqE+hOcwDQYJKoZIhvcNAQEFBQAw
PjELMAkGA1UEBhMCUEwxGzAZBgNVBAoTElVuaXpldG8gU3AuIHogby5vLjESMBAG
A1UEAxMJQ2VydHVtIENBMCIYDzIwMDkwMzAzMTMwNjEyWhgPMjAyNDAzMDMxMzA2
MTJaMH4xCzAJBgNVBAYTAlBMMSIwIAYDVQQKExlVbml6ZXRvIFRlY2hub2xvZ2ll
cyBTLkEuMScwJQYDVQQLEx5DZXJ0dW0gQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkx
IjAgBgNVBAMTGUNlcnR1bSBHbG9iYWwgU2VydmljZXMgQ0EwggEiMA0GCSqGSIb3
DQEBAQUAA4IBDwAwggEKAoIBAQC2WbjWcRnHoJcjIywSItrmuvILxCLKm1VuPTFB
I0275U7w2wFKlVlfuAuHHI+2cILXVzUjIu8CObDDAmiEax1S/BVe2n9s2+CZVX+A
buj6N6aDl05QAc52lXjXpKjK+9Fdx8vV+yD6Y273p2XnlxsibXzgKxYphWp9Lw25
3imjPts7emJ3VFyCujZAEppCQb2yNyEHiCsRpPO0x5a4YtZ4Hi9gP03q6girACza
MFWF5qe0UILRVm8k565nFSV1dZwXpOTogA1wQZrzHd8czfaQGqFAuao/H05FpQGF
bngkqChwqQ8XjsTyri1mJhyezqvdK9O15PzI/zIEl4GPT4XzAgMBAAGjggFsMIIB
aDAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBRFxbKGTszdKZfk3RTEbq5NuMF3
+DBSBgNVHSMESzBJoUKkQDA+MQswCQYDVQQGEwJQTDEbMBkGA1UEChMSVW5pemV0
byBTcC4geiBvLm8uMRIwEAYDVQQDEwlDZXJ0dW0gQ0GCAwEAIDAOBgNVHQ8BAf8E
BAMCAQYwLAYDVR0fBCUwIzAhoB+gHYYbaHR0cDovL2NybC5jZXJ0dW0ucGwvY2Eu
Y3JsMGgGCCsGAQUFBwEBBFwwWjAoBggrBgEFBQcwAYYcaHR0cDovL3N1YmNhLm9j
c3AtY2VydHVtLmNvbTAuBggrBgEFBQcwAoYiaHR0cDovL3JlcG9zaXRvcnkuY2Vy
dHVtLnBsL2NhLmNlcjA6BgNVHSAEMzAxMC8GBFUdIAAwJzAlBggrBgEFBQcCARYZ
aHR0cHM6Ly93d3cuY2VydHVtLnBsL0NQUzANBgkqhkiG9w0BAQUFAAOCAQEAdkAS
JUhem+q0pqo1NwySqtBsF3zHbnjHJSg0XgWeFIQ29r+C7OXsmvo5xGyVC9P367ZA
OIee86xq8nZ+cyanadrTixrL3A5D2nAdyi9NBiaVzqKoIKSiYGlOdB4p29Ij72sQ
I1+/5oHpvxPLf8ZKp2pAWvE+zyD3EUmTadyT/Jq0tmhfZQ3O6ZjHpjaU68Mh+mSY
eTayqMQMlBjg9E9whZqGDtAFtrBM+SFE1WGf9OsOsiLJx/dlhSeUWLKbzqMlvGry
lvIDrZJueSPZss+njbuL4ov9IghC0QbbM/DWcAFnp0EneYpQHO+/dNs4HVW1M0iX
U/r5z3rVPH9ZcaWOkg==
-----END CERTIFICATE-----
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            1a:d7:1f:b5:bb:5a:1d:59:5d:49:75:f4:f3:d4:2c:d2
    Signature Algorithm: sha1WithRSAEncryption
        Issuer: C=PL, O=Unizeto Technologies S.A., OU=Certum Certification Authority, CN=Certum Global Services CA
        Validity
            Not Before: May  6 12:00:00 2014 GMT
            Not After : Jul  4 10:31:40 2022 GMT
        Subject: C=PL, O=nazwa.pl S.A., OU=http://nazwa.pl, CN=nazwaSSL
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:cc:91:f5:f7:01:09:4f:75:c8:09:c7:14:8f:e4:
                    1a:99:78:20:99:40:59:6f:10:2f:ff:fe:d0:10:ff:
                    06:a3:39:3d:c4:f1:4b:07:cf:22:39:20:80:43:50:
                    c1:af:b4:01:71:a0:a3:30:11:52:d3:d2:98:d9:c2:
                    69:f7:e3:00:d9:19:3f:3d:b3:3b:52:75:e3:d3:0c:
                    ab:ff:57:01:3a:83:5c:f5:02:bb:28:fe:90:38:8e:
                    a2:84:cf:61:48:e7:99:e0:72:24:b6:11:58:4a:18:
                    57:0d:34:18:5e:35:c8:b3:ac:04:5f:8d:38:2f:a2:
                    cf:d2:dc:74:d8:41:02:ec:e0:db:0c:54:81:a4:7a:
                    c5:34:d5:19:86:b6:1e:65:f7:3c:f6:b2:dd:3a:b5:
                    b7:91:61:18:fd:81:2c:8a:68:d7:d6:a8:33:b7:47:
                    b8:f9:48:ad:35:ee:11:93:f9:c2:a9:fa:94:8e:4f:
                    bb:d1:1e:a7:64:74:b4:f9:0f:88:a7:11:a7:33:1a:
                    c2:b1:14:0c:12:a8:6b:82:44:78:4e:d5:79:8f:5c:
                    60:29:47:4c:36:35:52:c7:ad:6c:c0:20:39:93:f1:
                    c8:b3:3b:d9:c6:ec:dd:22:45:27:a2:50:12:07:f8:
                    fe:38:79:24:89:b9:f7:de:e0:c6:e9:64:e3:f4:0b:
                    fa:c7
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Basic Constraints: critical
                CA:TRUE, pathlen:0
            X509v3 Subject Key Identifier:
                9D:CE:F0:5A:B4:CB:25:CF:36:A5:82:5D:8F:F7:7F:98:46:19:37:2E
            X509v3 Authority Key Identifier:
                keyid:45:C5:B2:86:4E:CC:DD:29:97:E4:DD:14:C4:6E:AE:4D:B8:C1:77:F8

            X509v3 Key Usage: critical
                Certificate Sign, CRL Sign
            X509v3 CRL Distribution Points:

                Full Name:
                  URI:http://crl.certum.pl/gsca.crl

            Authority Information Access:
                OCSP - URI:http://subca.ocsp-certum.com
                CA Issuers - URI:http://repository.certum.pl/gsca.cer

            X509v3 Certificate Policies:
                Policy: X509v3 Any Policy
                  CPS: https://www.certum.pl/CPS

    Signature Algorithm: sha1WithRSAEncryption
         86:0a:5a:a0:d8:89:b7:55:46:b1:b4:b9:ef:3c:93:7f:73:d1:
         c5:26:6d:23:fe:80:1b:e5:61:69:d8:25:0c:b6:b5:6f:65:2c:
         ab:fc:8e:c1:dc:2e:ee:29:a2:ec:73:91:a3:65:c0:83:9c:6b:
         95:33:43:42:5a:f7:7f:5e:5a:eb:78:6a:60:00:31:e3:5b:34:
         9d:63:3b:81:74:ba:c0:93:bb:60:7a:aa:d1:ea:09:0f:d7:34:
         a0:c6:2f:f5:d6:ed:40:96:48:32:f3:f3:18:5b:be:40:56:66:
         ec:bb:3f:d8:18:84:9a:dd:2a:75:23:6b:21:4c:d9:1a:5c:93:
         52:99:11:75:0f:47:8a:83:9b:95:3f:59:bf:33:c2:b1:54:52:
         fa:ec:77:4a:22:50:db:40:dd:61:a3:f1:93:56:29:11:f3:f6:
         f8:1d:00:fd:e2:2e:af:91:15:30:b2:78:71:90:bf:6f:1c:81:
         65:d0:0c:32:69:91:da:26:e8:a8:89:82:8b:59:1c:70:ad:72:
         5f:54:23:45:a3:7f:d3:cb:4b:5d:5c:3d:83:d7:59:10:ba:1c:
         47:60:10:9a:4e:a0:8b:bf:dd:69:ce:bb:2c:fa:8f:c1:44:91:
         a6:78:ff:fe:50:ca:84:0b:0b:cf:53:d5:79:fe:48:ae:66:69:
         ef:63:9b:0f
-----BEGIN CERTIFICATE-----
MIIEoDCCA4igAwIBAgIQGtcftbtaHVldSXX089Qs0jANBgkqhkiG9w0BAQUFADB+
MQswCQYDVQQGEwJQTDEiMCAGA1UEChMZVW5pemV0byBUZWNobm9sb2dpZXMgUy5B
LjEnMCUGA1UECxMeQ2VydHVtIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MSIwIAYD
VQQDExlDZXJ0dW0gR2xvYmFsIFNlcnZpY2VzIENBMCIYDzIwMTQwNTA2MTIwMDAw
WhgPMjAyMjA3MDQxMDMxNDBaMFIxCzAJBgNVBAYTAlBMMRYwFAYDVQQKEw1uYXp3
YS5wbCBTLkEuMRgwFgYDVQQLEw9odHRwOi8vbmF6d2EucGwxETAPBgNVBAMTCG5h
endhU1NMMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzJH19wEJT3XI
CccUj+QamXggmUBZbxAv//7QEP8Gozk9xPFLB88iOSCAQ1DBr7QBcaCjMBFS09KY
2cJp9+MA2Rk/PbM7UnXj0wyr/1cBOoNc9QK7KP6QOI6ihM9hSOeZ4HIkthFYShhX
DTQYXjXIs6wEX404L6LP0tx02EEC7ODbDFSBpHrFNNUZhrYeZfc89rLdOrW3kWEY
/YEsimjX1qgzt0e4+UitNe4Rk/nCqfqUjk+70R6nZHS0+Q+IpxGnMxrCsRQMEqhr
gkR4TtV5j1xgKUdMNjVSx61swCA5k/HIszvZxuzdIkUnolASB/j+OHkkibn33uDG
6WTj9Av6xwIDAQABo4IBQDCCATwwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4E
FgQUnc7wWrTLJc82pYJdj/d/mEYZNy4wHwYDVR0jBBgwFoAURcWyhk7M3SmX5N0U
xG6uTbjBd/gwDgYDVR0PAQH/BAQDAgEGMC4GA1UdHwQnMCUwI6AhoB+GHWh0dHA6
Ly9jcmwuY2VydHVtLnBsL2dzY2EuY3JsMGoGCCsGAQUFBwEBBF4wXDAoBggrBgEF
BQcwAYYcaHR0cDovL3N1YmNhLm9jc3AtY2VydHVtLmNvbTAwBggrBgEFBQcwAoYk
aHR0cDovL3JlcG9zaXRvcnkuY2VydHVtLnBsL2dzY2EuY2VyMDoGA1UdIAQzMDEw
LwYEVR0gADAnMCUGCCsGAQUFBwIBFhlodHRwczovL3d3dy5jZXJ0dW0ucGwvQ1BT
MA0GCSqGSIb3DQEBBQUAA4IBAQCGClqg2Im3VUaxtLnvPJN/c9HFJm0j/oAb5WFp
2CUMtrVvZSyr/I7B3C7uKaLsc5GjZcCDnGuVM0NCWvd/XlrreGpgADHjWzSdYzuB
dLrAk7tgeqrR6gkP1zSgxi/11u1Alkgy8/MYW75AVmbsuz/YGISa3Sp1I2shTNka
XJNSmRF1D0eKg5uVP1m/M8KxVFL67HdKIlDbQN1ho/GTVikR8/b4HQD94i6vkRUw
snhxkL9vHIFl0AwyaZHaJuioiYKLWRxwrXJfVCNFo3/Ty0tdXD2D11kQuhxHYBCa
TqCLv91pzrss+o/BRJGmeP/+UMqECwvPU9V5/kiuZmnvY5sP
-----END CERTIFICATE-----
"""
