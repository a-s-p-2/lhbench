#!/bin/bash

echo "Starting sbt wrapper script..."

# Kill any existing sbt servers
echo "Killing existing sbt servers..."
pkill -f sbt || true

# Remove server state directories
echo "Cleaning server state directories..."
rm -rf ~/.sbt/1.0/server ~/.sbt/boot project/.sbtboot project/.boot || true

# Set environment variables
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export SBT_OPTS="-Dsbt.server=false -Dsbt.client=false -Dsbt.server.autostart=false"

echo "JAVA_HOME: $JAVA_HOME"
echo "SBT_OPTS: $SBT_OPTS"
echo "Running: sbt $@"

# Run sbt with automatic 'n' response to server prompts
printf 'n\nn\nn\n' | timeout 300 sbt "$@"