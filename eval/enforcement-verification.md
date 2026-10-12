# Enforcement Verification

## Layer 1: Container Permissions

**Role:** documentation-auditor

**Workspace check**

**Command:** 

touch /workspace/should-fail.txt

**Output:**

touch: cannot touch '/workspace/should-fail.txt': Read-only file system

**Memory volume check**

**Command:**

if grep -qE ' /memory(/| )' /proc/self/mountinfo; then
echo "/memory is mounted"
else
echo "/memory is not mounted"
fi

**Output:**

/memory is not mounted

**Result:** 

Blocked as expected — workspace writes fail with a read-only file system error, and the /memory mount is absent.


## Layer 2: MCP Server Allow-Lists

**Denied operation check**

**Command:**

npx @modelcontextprotocol/inspector --cli python mcp-servers/storage/server.py \
-e AGENT_ROLE=documentation-auditor \
-e STORAGE_AUDIT_LOG=/tmp/storage-audit-log.jsonl \
-e STORAGE_STORE=/tmp/storage-store.json \
--method tools/call --tool-name write_entry \
--tool-arg key=probe --tool-arg value=should-be-denied

**Output:**

authorization_denied: role 'documentation-auditor' may not call 'write_entry'.

**Status:** PASS

**Granted operation check**

**Command:** Test list_entries as documentation-auditor.

**Output:** Pending verification.

**Status:** PENDING

**Classification ceiling check**

**Command:** Query a confidential document using the retrieval server as documentation-auditor.

**Output:** Confidential results withheld; internal results permitted.

**Status:** PENDING

**Audit log tail:**

**Command:**
tail -n 5 /tmp/storage-audit-log.jsonl

**Output:** 
Two authorization_denied records for documentation-auditor attempting write_entry.

**Status:** PASS