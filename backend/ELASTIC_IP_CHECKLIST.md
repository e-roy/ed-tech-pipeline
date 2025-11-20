# Elastic IP Allocation Checklist

## Why This Is Critical

The current EC2 instance IP `13.58.115.166` is **NOT an Elastic IP**. This means:
- ❌ IP will change if instance restarts
- ❌ API Gateway integration will break
- ❌ Frontend will lose connection

**Solution**: Allocate and associate an Elastic IP before setting up API Gateway.

---

## Step-by-Step Checklist

### Step 1: Allocate Elastic IP

- [ ] Log into AWS Console
- [ ] Navigate to: **EC2** → **Network & Security** → **Elastic IPs**
- [ ] Click **"Allocate Elastic IP address"**
- [ ] Select **"Amazon's pool of IPv4 addresses"**
- [ ] Click **"Allocate"**
- [ ] **Note the new Elastic IP address** (e.g., `54.123.45.67`)

### Step 2: Associate Elastic IP with Instance

- [ ] Select the newly allocated Elastic IP
- [ ] Click **"Actions"** → **"Associate Elastic IP address"**
- [ ] In **"Instance"** dropdown, select: `i-051a27d0f69e98ca2`
- [ ] In **"Private IP address"**, select: `172.31.40.134` (current private IP)
- [ ] Click **"Associate"**

### Step 3: Verify Association

- [ ] Check that instance now shows the Elastic IP as Public IP
- [ ] Verify old IP `13.58.115.166` is no longer associated
- [ ] Run verification command:
  ```bash
  aws ec2 describe-instances \
    --instance-ids i-051a27d0f69e98ca2 \
    --profile default1 \
    --region us-east-2 \
    --query 'Reservations[0].Instances[0].PublicIpAddress'
  ```

### Step 4: Update All References

- [ ] Update API Gateway integration URLs (use new Elastic IP)
- [ ] Update documentation (README.md, etc.)
- [ ] Update scripts (update_ec2.sh, etc.)
- [ ] Update any hardcoded IPs in code
- [ ] **DO NOT** update until Elastic IP is confirmed working

### Step 5: Test Backend Accessibility

- [ ] Test HTTP endpoint: `curl http://<new-elastic-ip>:8000/health`
- [ ] Test WebSocket endpoint: `wscat -c ws://<new-elastic-ip>:8000/ws/test`
- [ ] Verify backend responds correctly
- [ ] Check EC2 logs for any connection issues

---

## Important Notes

1. **Timing**: Do this BEFORE creating API Gateway integrations
2. **Cost**: Elastic IPs are free when associated with a running instance
3. **Old IP**: The old IP `13.58.115.166` will be released automatically
4. **DNS**: If using any DNS records, update them after association

---

## Rollback (If Needed)

If something goes wrong:
1. Disassociate Elastic IP from instance
2. Release Elastic IP (if not needed)
3. Instance will get a new dynamic IP
4. Update references back to new dynamic IP

---

## Verification Commands

```bash
# Check current Elastic IP association
aws ec2 describe-addresses \
  --filters "Name=instance-id,Values=i-051a27d0f69e98ca2" \
  --profile default1 \
  --region us-east-2

# Check instance public IP
aws ec2 describe-instances \
  --instance-ids i-051a27d0f69e98ca2 \
  --profile default1 \
  --region us-east-2 \
  --query 'Reservations[0].Instances[0].[PublicIpAddress,PublicDnsName]' \
  --output table
```

---

## Next Steps After Elastic IP Allocation

1. ✅ Update API Gateway integration URLs with new Elastic IP
2. ✅ Update frontend environment variables
3. ✅ Test all endpoints
4. ✅ Document new IP in project README

