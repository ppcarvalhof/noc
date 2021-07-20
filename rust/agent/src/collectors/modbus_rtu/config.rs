// ---------------------------------------------------------------------
// ModbusRtuConfig
// ---------------------------------------------------------------------
// Copyright (C) 2007-2021 The NOC Project
// See LICENSE for details
// ---------------------------------------------------------------------

use crate::proto::modbus::ModbusFormat;
use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
pub struct ModbusRtuConfig {
    pub serial_path: String,
    pub slave: u8,
    pub baud_rate: u32,
    pub data_bits: usize, // 5,6,7,8
    #[serde(default = "default_none")]
    pub parity: CfgParity,
    pub stop_bits: usize, // 1, 2
    pub register: u16,
    #[serde(default = "default_1")]
    pub count: u16,
    #[serde(default = "default_holding")]
    pub register_type: RegisterType,
    pub format: ModbusFormat,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
#[serde(tag = "request_type")]
pub enum RegisterType {
    Holding,
    Input,
    Coil,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
#[serde(tag = "parity")]
pub enum CfgParity {
    None,
    Odd,
    Even,
}

fn default_1() -> u16 {
    1
}

fn default_holding() -> RegisterType {
    RegisterType::Holding
}

fn default_none() -> CfgParity {
    CfgParity::None
}
