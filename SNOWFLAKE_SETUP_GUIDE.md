# 🏔️ Snowflake Account Setup Guide

This guide walks you through getting your Snowflake connection details from the Snowflake website, step by step.

## 📋 What You'll Need

By the end of this guide, you'll have:
- ✅ Account Identifier
- ✅ Username
- ✅ Password
- ✅ Warehouse Name
- ✅ Database Name
- ✅ Schema Name

---

## 🆕 Option 1: Create a New Snowflake Account (Free Trial)

### Step 1: Sign Up for Snowflake Free Trial

1. **Go to Snowflake Website**
   - Visit: https://signup.snowflake.com/
   - Or go to: https://www.snowflake.com/ and click "Start for Free"

2. **Choose Your Edition**
   - Select **Standard** (recommended for this project)
   - Or select **Enterprise** if you need advanced features

3. **Choose Your Cloud Provider**
   - Select **AWS**, **Azure**, or **Google Cloud**
   - Choose a region close to your location for better performance
   - Example: `US East (N. Virginia)` for AWS

4. **Fill Out Registration Form**
   - First Name
   - Last Name
   - Email Address (this will be your username)
   - Company Name
   - Role/Title
   - Country

5. **Click "CONTINUE"**

6. **Check Your Email**
   - Look for email from Snowflake with subject "Activate your Snowflake account"
   - Click the activation link

7. **Set Your Password**
   - Create a strong password
   - Confirm password
   - Click "Get Started"

8. **Welcome Screen**
   - You'll see a welcome screen with a tour
   - You can skip the tour or follow it

### Step 2: Get Your Account Identifier

Once logged in:

1. **Look at Your Browser URL**
   - The URL will look like: `https://app.snowflake.com/XXXXXXX/YYYYYYY/`
   - Or: `https://XXXXXXX.snowflakecomputing.com/`

2. **Find Your Account Identifier**
   
   **Method A: From URL**
   - If URL is `https://xy12345.us-east-1.snowflakecomputing.com/`
   - Your account identifier is: `xy12345.us-east-1`
   
   **Method B: From Snowflake UI**
   - Click your name in the bottom left corner
   - Hover over your account name
   - You'll see the full account identifier
   - Example: `ORGNAME-ACCOUNTNAME` or `xy12345.us-east-1`

3. **Copy Your Account Identifier**
   - Write it down or copy it
   - Format: `<account_locator>.<region>.<cloud>`
   - Example: `xy12345.us-east-1.aws` or just `xy12345.us-east-1`

### Step 3: Get Your Username

Your username is typically:
- The email address you used to sign up
- Or a username you created during setup

To verify:
1. Click your profile icon (bottom left)
2. Your username is displayed there

### Step 4: Create a Warehouse

1. **Navigate to Warehouses**
   - Click "Admin" in the left sidebar
   - Click "Warehouses"
   - Or go to: `https://<your-account>.snowflakecomputing.com/#/compute/warehouses`

2. **Create New Warehouse**
   - Click "+ Warehouse" button (top right)
   
3. **Configure Warehouse**
   - **Name**: `COMPUTE_WH` (recommended) or any name you prefer
   - **Size**: Select `X-Small` (sufficient for this project)
   - **Auto Suspend**: 5 minutes (default)
   - **Auto Resume**: Checked (default)
   - **Comment**: "Warehouse for AI Home Inspection Dashboard"

4. **Click "Create Warehouse"**

5. **Note Your Warehouse Name**
   - Write down: `COMPUTE_WH` (or whatever you named it)

### Step 5: Create a Database

1. **Navigate to Databases**
   - Click "Data" in the left sidebar
   - Click "Databases"
   - Or go to: `https://<your-account>.snowflakecomputing.com/#/data/databases`

2. **Create New Database**
   - Click "+ Database" button (top right)

3. **Configure Database**
   - **Name**: `HOME_INSPECTION_DB`
   - **Comment**: "Database for AI Home Inspection application"

4. **Click "Create"**

5. **Note Your Database Name**
   - Write down: `HOME_INSPECTION_DB`

### Step 6: Verify Schema

1. **Click on Your Database**
   - Click `HOME_INSPECTION_DB` in the database list

2. **Check Schemas**
   - You should see a `PUBLIC` schema (created by default)
   - This is what you'll use

3. **Note Your Schema Name**
   - Write down: `PUBLIC`

### Step 7: Enable Cortex AI (Important!)

1. **Check Cortex AI Availability**
   - Cortex AI is available in most regions
   - Check: https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability

2. **Verify Your Region Supports Cortex**
   - If your region doesn't support Cortex, you may need to:
     - Create a new account in a supported region
     - Or contact Snowflake support

3. **Test Cortex AI**
   - Click "Worksheets" in the left sidebar
   - Create a new worksheet
   - Run this test query:
   ```sql
   SELECT SNOWFLAKE.CORTEX.COMPLETE('llama2-70b-chat', 'Hello, how are you?');
   ```
   - If it works, Cortex AI is enabled!

---

## 🔑 Option 2: Use Existing Snowflake Account

### Step 1: Log In to Snowflake

1. **Go to Your Snowflake Login Page**
   - If you know your account URL: `https://<account>.snowflakecomputing.com/`
   - Or go to: https://app.snowflake.com/ and enter your account identifier

2. **Enter Credentials**
   - Username
   - Password
   - Click "Sign In"

### Step 2: Find Your Account Identifier

1. **Method A: From URL**
   - Look at your browser URL after logging in
   - Example: `https://xy12345.us-east-1.snowflakecomputing.com/`
   - Account identifier: `xy12345.us-east-1`

2. **Method B: From Account Menu**
   - Click your name/profile (bottom left corner)
   - Hover over your account name
   - Copy the account identifier shown

3. **Method C: From Admin Panel**
   - Click "Admin" → "Accounts"
   - Your account identifier is listed there

### Step 3: Find Your Username

1. **Click Profile Icon** (bottom left)
2. Your username is displayed
3. Write it down

### Step 4: Find or Create Warehouse

1. **Navigate to Warehouses**
   - Click "Admin" → "Warehouses"

2. **Check Existing Warehouses**
   - Look for an existing warehouse you can use
   - Common names: `COMPUTE_WH`, `ANALYTICS_WH`, `DEV_WH`

3. **Or Create New Warehouse** (if needed)
   - Click "+ Warehouse"
   - Name: `HOME_INSPECTION_WH`
   - Size: `X-Small`
   - Click "Create Warehouse"

4. **Note Warehouse Name**
   - Write down the warehouse name you'll use

### Step 5: Find or Create Database

1. **Navigate to Databases**
   - Click "Data" → "Databases"

2. **Check Existing Databases**
   - Look for a database you can use
   - Or create a new one

3. **Create New Database** (if needed)
   - Click "+ Database"
   - Name: `HOME_INSPECTION_DB`
   - Click "Create"

4. **Note Database Name**
   - Write down: `HOME_INSPECTION_DB`

### Step 6: Verify Schema

1. **Click Your Database**
2. **Check Schemas Tab**
   - Default schema is usually `PUBLIC`
3. **Note Schema Name**
   - Write down: `PUBLIC`

---

## 📝 Summary: Your Connection Details

After completing the steps above, you should have:

```
Account Identifier: xy12345.us-east-1
Username: your.email@example.com
Password: ••••••••••••
Warehouse: COMPUTE_WH
Database: HOME_INSPECTION_DB
Schema: PUBLIC
```

---

## 🔧 Configure Your Dashboard

Now that you have your Snowflake details, configure the dashboard:

### Option A: Using Streamlit Secrets (Recommended)

1. **Copy the template**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml`**
   ```toml
   [connections.snowflake]
   account = "xy12345.us-east-1"           # Your account identifier
   user = "your.email@example.com"         # Your username
   password = "your_password_here"         # Your password
   warehouse = "COMPUTE_WH"                # Your warehouse name
   database = "HOME_INSPECTION_DB"         # Your database name
   schema = "PUBLIC"                       # Your schema name
   ```

3. **Save the file**

### Option B: Using Environment Variables

```bash
export SNOWFLAKE_ACCOUNT="xy12345.us-east-1"
export SNOWFLAKE_USER="your.email@example.com"
export SNOWFLAKE_PASSWORD="your_password_here"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="HOME_INSPECTION_DB"
export SNOWFLAKE_SCHEMA="PUBLIC"
```

---

## 🗄️ Initialize Database Schema

Before running the dashboard, initialize the database:

### Method 1: Using SnowSQL (Command Line)

1. **Install SnowSQL** (if not already installed)
   - Download from: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html

2. **Run Schema Script**
   ```bash
   snowsql -a xy12345.us-east-1 -u your.email@example.com -f schema/init_schema.sql
   ```

3. **Enter Password** when prompted

### Method 2: Using Snowflake Web UI

1. **Open Snowflake Web UI**
   - Click "Worksheets" in left sidebar

2. **Create New Worksheet**
   - Click "+ Worksheet"

3. **Set Context**
   ```sql
   USE DATABASE HOME_INSPECTION_DB;
   USE SCHEMA PUBLIC;
   USE WAREHOUSE COMPUTE_WH;
   ```

4. **Copy and Paste Schema**
   - Open `schema/init_schema.sql` in a text editor
   - Copy all contents
   - Paste into Snowflake worksheet

5. **Run All Statements**
   - Click "Run All" or press Ctrl+Enter

6. **Verify Tables Created**
   ```sql
   SHOW TABLES;
   ```
   - You should see: `properties`, `rooms`, `findings`, `defect_tags`, `classification_history`, `error_log`

---

## ✅ Verify Setup

Test your connection:

1. **Run Dashboard**
   ```bash
   ./run_dashboard.sh
   ```

2. **Check Connection**
   - Dashboard should show "✅ Connected to Snowflake"
   - No error messages

3. **Generate Sample Data** (optional)
   ```bash
   python tests/generate_sample_data.py
   ```

4. **View Properties**
   - Dashboard should display sample properties
   - Try filtering and searching

---

## 🔍 Troubleshooting

### Issue: "Invalid account identifier"

**Solution:**
- Verify account identifier format
- Should be: `<account_locator>.<region>` or `<account_locator>.<region>.<cloud>`
- Example: `xy12345.us-east-1` or `xy12345.us-east-1.aws`
- Don't include `https://` or `.snowflakecomputing.com`

### Issue: "Authentication failed"

**Solution:**
- Verify username (usually your email)
- Check password (case-sensitive)
- Try logging in via web UI first to confirm credentials

### Issue: "Warehouse does not exist"

**Solution:**
- Verify warehouse name (case-sensitive)
- Check warehouse exists: Go to Admin → Warehouses
- Create warehouse if needed (see Step 4 above)

### Issue: "Database does not exist"

**Solution:**
- Verify database name (case-sensitive)
- Check database exists: Go to Data → Databases
- Create database if needed (see Step 5 above)

### Issue: "Cortex AI functions not available"

**Solution:**
- Check your region supports Cortex AI
- See: https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability
- May need to create account in different region

---

## 📞 Additional Resources

- **Snowflake Documentation**: https://docs.snowflake.com/
- **Snowflake Free Trial**: https://signup.snowflake.com/
- **Cortex AI Documentation**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview
- **SnowSQL Installation**: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html
- **Snowflake Community**: https://community.snowflake.com/

---

## 🎯 Next Steps

After completing this setup:

1. ✅ You have all Snowflake connection details
2. ✅ Database schema is initialized
3. ✅ Dashboard is configured
4. ✅ Ready to run the dashboard!

**Run the dashboard:**
```bash
./run_dashboard.sh
```

**Happy inspecting! 🏠✨**
