# AWS Cloud Web Application with Monitoring and Backup

## Internship Project

A cloud-based web application deployed on **Amazon Web Services (AWS)** using **Amazon EC2 and Nginx**, with monitoring, alerting, backup, log analysis, security, and cost-control features.

---

## 📌 Project Overview

This project demonstrates how a web application can be deployed and managed on AWS using cloud infrastructure while maintaining:

* Reliable web hosting
* Application health monitoring
* Resource monitoring and alerting
* Automated backup support
* Centralized log monitoring
* Log analysis
* Access control using IAM
* Object storage using Amazon S3
* Cloud cost monitoring

The project was designed using AWS Free Tier-compatible services.

---

## 🎯 Problem Statement

Web applications require a reliable hosting environment along with monitoring, backup, security, and cost management.

A basic web server alone does not provide sufficient visibility into server health, application availability, logs, backup status, or cloud spending.

The objective of this project is to build a simple AWS-based web application with monitoring and backup capabilities while keeping the infrastructure simple and cost-conscious.

---

## 💡 Project Solution

The project uses an Amazon EC2 instance to host a web application using Nginx.

AWS services are integrated to provide:

1. Web application hosting
2. Server monitoring
3. CloudWatch alarms
4. SNS email notifications
5. S3 object storage
6. EBS snapshot backup
7. Nginx log analysis
8. IAM-based access control
9. AWS Budget monitoring

This provides a complete demonstration of a monitored and backed-up cloud web application.

---

## ☁️ AWS Services Used

| AWS Service           | Purpose                              |
| --------------------- | ------------------------------------ |
| **Amazon EC2**        | Hosts the web application            |
| **Amazon VPC**        | Provides network infrastructure      |
| **Amazon S3**         | Stores project/log data              |
| **Amazon IAM**        | Manages permissions and access       |
| **Amazon CloudWatch** | Monitors EC2 resources               |
| **Amazon SNS**        | Sends monitoring email notifications |
| **Amazon EBS**        | Provides EC2 storage                 |
| **EBS Snapshot**      | Provides backup capability           |
| **AWS Budgets**       | Monitors cloud spending              |
| **Nginx**             | Web server                           |
| **Python**            | Log analysis and validation scripts  |
| **Shell Script**      | Server setup and automation          |

---

## 🏗️ Architecture

The main architecture consists of:

```text
                         Internet
                            |
                            v
                    +---------------+
                    |   Amazon VPC   |
                    |  10.0.0.0/16  |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Public Subnet  |
                    | 10.0.1.0/24   |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Amazon EC2     |
                    | Ubuntu + Nginx |
                    +-------+-------+
                            |
                 +----------+----------+
                 |                     |
                 v                     v
          Web Application         Nginx Logs
                                      |
                                      v
                              Log Analysis Script
                                      |
                                      v
                                  Amazon S3

EC2
 |
 +----> CloudWatch ----> SNS Email Alert
 |
 +----> EBS Snapshot ----> Backup
 |
 +----> AWS Budget ----> Cost Monitoring
```

---

## 🚀 Project Features

### 1. Web Application Hosting

The web application is hosted on an Amazon EC2 instance using Nginx.

The application includes:

* Main web page
* Health check page
* Responsive styling
* JavaScript functionality

---

### 2. EC2 Server

An Ubuntu-based EC2 instance is used as the main web server.

Nginx is installed and configured to serve the application.

---

### 3. CloudWatch Monitoring

Amazon CloudWatch is used to monitor EC2 health and CPU utilization.

Configured alarms include:

* **CPU Utilization High Alarm**
* **EC2 Status Check Failed Alarm**

The CPU alarm is configured to detect high CPU utilization.

---

### 4. SNS Notifications

Amazon SNS is connected to the CloudWatch alarms.

When a configured alarm condition occurs, an email notification can be sent to the subscribed email address.

---

### 5. S3 Storage

Amazon S3 is used for storing project-related log data and supporting cloud storage requirements.

---

### 6. Backup

An EBS snapshot is used to provide a backup of the EC2 storage volume.

This demonstrates how the server data can be backed up for recovery purposes.

---

### 7. Nginx Log Analysis

The project includes a Python-based log analysis script.

The script analyzes Nginx access logs and extracts useful information such as:

* Request information
* HTTP status codes
* Request statistics
* Log activity

Example script:

```text
scripts/analyze_logs.py
```

---

### 8. IAM Security

AWS IAM is used to control access to AWS resources.

An EC2 IAM role and policy are included as part of the project configuration.

---

### 9. Cost Monitoring

AWS Budget is configured to monitor cloud spending and help prevent unexpected costs.

The project is designed around a minimal AWS infrastructure suitable for a student internship demonstration.

---

## 📂 Project Structure

```text
aws-cloud-web-application/
│
├── dataset/
│   └── web-access-logs.csv
│
├── documentation/
│   ├── architecture.md
│   ├── backup-restore.md
│   ├── cost-control.md
│   ├── deployment.md
│   ├── monitoring.md
│   ├── presentation.md
│   ├── screenshot-checklist.md
│   ├── security.md
│   ├── testing.md
│   └── validation-report.md
│
├── iam/
│   ├── policies/
│   │   └── ec2-s3-policy.json
│   └── README.md
│
├── infrastructure/
│   ├── cloudformation-stack.yaml
│   ├── deploy.md
│   └── README.md
│
├── monitoring/
│   └── README.md
│
├── scripts/
│   ├── analyze_logs.py
│   ├── backup-logs.sh
│   ├── setup-server.sh
│   ├── upload-to-s3.sh
│   ├── validate_cfn.py
│   └── validate_scripts.py
│
├── web-app/
│   ├── index.html
│   ├── health.html
│   ├── script.js
│   └── style.css
│
└── .gitignore
```

---

## 🛠️ Technologies Used

* HTML5
* CSS3
* JavaScript
* Python
* Bash/Shell scripting
* Nginx
* Git
* GitHub
* Amazon Web Services

---

## 🔐 Security Considerations

The repository does not contain private AWS credentials or secret access keys.

Sensitive information such as:

* AWS Secret Access Keys
* Private SSH keys
* Passwords
* Environment secrets

should not be committed to the repository.

IAM roles and policies are used to provide controlled access to AWS resources.

---

## 📊 Monitoring and Backup

The project demonstrates three important cloud-management areas:

### Monitoring

```text
EC2
 ↓
CloudWatch
 ↓
Alarm
 ↓
SNS
 ↓
Email Notification
```

### Backup

```text
EC2 Storage
 ↓
EBS Volume
 ↓
EBS Snapshot
 ↓
Backup
```

### Log Analysis

```text
Nginx
 ↓
Access Logs
 ↓
Python Analysis Script
 ↓
Log Statistics / CSV
```

---

## 🧪 Testing

The project includes validation and testing documentation covering:

* Web application availability
* EC2 health
* Nginx service
* CloudWatch monitoring
* SNS notifications
* S3 storage
* Backup configuration
* Log analysis
* Infrastructure configuration

Detailed testing information is available in the `documentation/` directory.

---

## 📸 Project Screenshots

Screenshots demonstrating the project implementation and AWS services are included in the internship project report.

Important screenshots include:

* Web application
* EC2 instance
* Nginx
* S3 bucket
* IAM role
* CloudWatch alarms
* SNS notification
* EBS snapshot
* AWS Budget
* Nginx log analysis

---

## 🎥 Project Explanation Video

A 4–5 minute project explanation video is included as part of the internship submission.

The video demonstrates:

* Project introduction
* Problem statement
* Solution
* AWS architecture
* Web application
* AWS services
* Monitoring
* Backup
* Log analysis
* Final output

---

## 📄 Project Documentation

Detailed documentation is available in the `documentation/` folder.

It includes:

* Architecture
* Deployment
* Monitoring
* Backup and restore
* Security
* Cost control
* Testing
* Validation

---

## 🌐 Project Repository

GitHub Repository:

https://github.com/shukriyashaik91-arch/aws-cloud-web-application

---

## 👩‍💻 Project Type

**AWS Cloud Internship Project**

### Project Title

**AWS Cloud Web Application with Monitoring and Backup**

### Domain

**Cloud Computing / AWS**

---

## 📌 Conclusion

This project demonstrates the deployment of a web application on AWS with supporting cloud services for monitoring, notification, storage, backup, security, log analysis, and cost management.

It provides practical experience with AWS infrastructure and demonstrates how different AWS services can work together to support a cloud-hosted web application.
