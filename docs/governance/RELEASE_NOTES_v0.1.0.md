# Release Notes - v0.1.0

## Description
This release establishes the baseline core infrastructure of Flock. Version 0.1.0 provides a secure, typed, asynchronous TCP transport and serialization engine, along with request-response correlation mapping for remote procedure calls (RPC).

## Features Added
- Pydantic v2 Cluster Configuration Validation models.
- Custom binary message protocol framing with magic bytes `b"FLOK"`.
- Fully asynchronous TCP network streams implementing transport interfaces.
- Built-in JSON and MessagePack serializing interfaces.
- Transport-independent `MessageBus` coordinating middleware pipelines and RPCs.
- Dynamic `MessageRouter` registry mapping.
- Local Event Bus supporting decoupled internal publishing.

## Upgrading from Previous Versions
Not applicable. This is the initial framework release.
