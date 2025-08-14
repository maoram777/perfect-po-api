# 🔐 GitHub Secrets Setup Guide

This guide explains how to set up GitHub repository secrets for deploying your Perfect PO API to AWS ECS.

## 🎯 **Why GitHub Secrets Instead of AWS Secrets Manager?**

**Benefits:**
- ✅ **Simpler setup** - No need to create AWS secrets
- ✅ **Centralized management** - All secrets in one place
- ✅ **Easier updates** - Change secrets without touching AWS
- ✅ **Better security** - GitHub encrypts secrets at rest
- ✅ **Team access** - Repository admins can manage secrets

## 📋 **Required GitHub Secrets**

### **1. AWS Credentials**
```
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_ACCOUNT_ID=your_aws_account_id
```

### **2. Application Secrets**
```
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET_KEY=your_jwt_secret_key
KEEPA_API_KEY=your_keepa_api_key
```

## 🚀 **Step-by-Step Setup**

### **Step 1: Go to Your GitHub Repository**
1. Navigate to your repository on GitHub
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**

### **Step 2: Add AWS Credentials**

#### **AWS_ACCESS_KEY_ID**
1. Click **New repository secret**
2. **Name**: `AWS_ACCESS_KEY_ID`
3. **Value**: Your AWS access key ID
4. Click **Add secret**

#### **AWS_SECRET_ACCESS_KEY**
1. Click **New repository secret**
2. **Name**: `AWS_SECRET_ACCESS_KEY`
3. **Value**: Your AWS secret access key
4. Click **Add secret**

#### **AWS_ACCOUNT_ID**
1. Click **New repository secret**
2. **Name**: `AWS_ACCOUNT_ID`
3. **Value**: Your AWS account ID (12-digit number)
4. Click **Add secret**

### **Step 3: Add Application Secrets**

#### **MONGODB_URI**
1. Click **New repository secret**
2. **Name**: `MONGODB_URI`
3. **Value**: Your MongoDB Atlas connection string
   ```
   mongodb+srv://maor:Mvnu3GxLmlDm251O@allshoes-dev.gvdqclc.mongodb.net/?retryWrites=true&w=majority&appName=AllShoes-Dev
   ```
4. Click **Add secret**

#### **JWT_SECRET_KEY**
1. Click **New repository secret**
2. **Name**: `JWT_SECRET_KEY`
3. **Value**: A strong, random secret key (at least 32 characters)
   ```
   your_super_secret_jwt_key_here_make_it_long_and_random
   ```
4. Click **Add secret**

#### **KEEPA_API_KEY**
1. Click **New repository secret**
2. **Name**: `KEEPA_API_KEY`
3. **Value**: Your Keepa API key
4. Click **Add secret**

## 🔍 **How It Works**

### **1. GitHub Actions Workflow**
- Reads secrets from GitHub repository
- Replaces placeholders in task definition template
- Deploys with actual secret values

### **2. Secret Injection Process**
```bash
# Template with placeholders
"Value": "MONGODB_URI_PLACEHOLDER"

# GitHub Actions replaces with actual secret
"Value": "mongodb+srv://actual_connection_string"
```

### **3. ECS Task Definition**
- Secrets are injected as environment variables
- Container receives actual values at runtime
- No secrets stored in AWS (only in GitHub)

## 🛡️ **Security Best Practices**

### **1. Secret Management**
- ✅ **Never commit secrets** to your code
- ✅ **Use strong, unique values** for each secret
- ✅ **Rotate secrets regularly** (especially AWS keys)
- ✅ **Limit access** to repository secrets

### **2. AWS IAM Best Practices**
- ✅ **Use least privilege** - Only necessary permissions
- ✅ **Create dedicated IAM user** for deployments
- ✅ **Enable MFA** on AWS account
- ✅ **Monitor access** with CloudTrail

### **3. Repository Security**
- ✅ **Enable branch protection** on main branch
- ✅ **Require pull request reviews**
- ✅ **Use GitHub security features** (Dependabot, etc.)

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. "Secret not found" Error**
- Check secret name spelling (case-sensitive)
- Verify secret exists in repository settings
- Ensure workflow has access to secrets

#### **2. "Invalid secret value" Error**
- Check secret value format
- Ensure no extra spaces or characters
- Verify special characters are properly escaped

#### **3. "AWS credentials invalid" Error**
- Verify AWS access key and secret
- Check AWS account ID
- Ensure IAM user has necessary permissions

### **Debugging Steps**
1. **Check workflow logs** for specific error messages
2. **Verify secret names** match exactly
3. **Test AWS credentials** locally with AWS CLI
4. **Check IAM permissions** for deployment user

## 📱 **Testing Your Setup**

### **1. Manual Workflow Trigger**
1. Go to **Actions** tab in your repository
2. Click on **Deploy to AWS ECS (GitHub Secrets)**
3. Click **Run workflow**
4. Select your branch and environment
5. Monitor the deployment

### **2. Verify Deployment**
- Check ECS service status
- Test health endpoint
- Verify environment variables in container

## 🎉 **Success!**

Once all secrets are configured:
- ✅ **Push to main branch** triggers automatic deployment
- ✅ **Secrets are securely injected** into your containers
- ✅ **No AWS Secrets Manager setup** required
- ✅ **Centralized secret management** in GitHub

## 🔄 **Updating Secrets**

### **To Change a Secret:**
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Find the secret you want to update
3. Click **Update**
4. Enter new value
5. Click **Update secret**
6. **Next deployment** will use the new value

### **To Add New Secrets:**
1. Follow the same process as initial setup
2. Update your task definition template if needed
3. Update GitHub Actions workflow if needed

---

**Your Perfect PO API is now ready for secure, automated deployment using GitHub secrets! 🚀**
