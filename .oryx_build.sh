apt-get update && apt-get install -y unixodbc-dev
# Install general ODBC libraries
apt-get update && apt-get install -y unixodbc-dev

# Download and install the Microsoft SQL Server ODBC driver for Debian 11 (Bookworm)
# This is required for pyodbc to connect to Azure SQL Database.
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17