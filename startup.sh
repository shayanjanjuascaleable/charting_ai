#!/bin/bash

# Ye script Azure App Service jaisi Linux environment mein ODBC drivers install karega
# takay pyodbc sahi tarah kaam kar sakay.

# Update the package list
sudo apt-get update -y

# Install tools needed for a secure connection
sudo apt-get install curl apt-transport-https debconf-utils -y

# Install the Microsoft ODBC Driver for SQL Server
# Add the Microsoft package repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Update the package list again to include the new repository
sudo apt-get update -y

# Install the ODBC driver and the ODBC development headers
# The development headers are crucial for pyodbc to build correctly
sudo ACCEPT_EULA=Y apt-get install msodbcsql17 unixodbc-dev -y

# Run the default Oryx startup script to install Python dependencies
# and start the application
# Is mein aapka requirements.txt file use hoga
/opt/startup/startup.sh

