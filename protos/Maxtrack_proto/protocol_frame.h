#ifndef _PROTOCOL_FRAME_
#define _PROTOCOL_FRAME_

#include <stdint.h> 
#include <stdbool.h>

#define HEADER_VALUE             0xAA55AA55


#define CRYPTO_NONE              0
#define CRYPTO_AES128            1

#define COMPRESS_NONE            0
#define COMPRESS_ZLIB            1

#define ACK_NOT_REQUIRED         0
#define ACK_REQUIRED             1


#define MAXPB_CMD_KEEP_ALIVE                 0x0000   //message BasicCommand
#define MAXPB_CMD_POSITION                   0x0001   //message MultipleReportData

#define MAXPB_CMD_ACK                        0x0002   //message Ack
#define MAXPB_CMD_NACK                       0x0003   //message Nack

#define MAXPB_CMD_GENERATE_POSITION          0x0004   //message BasicCommand
#define MAXPB_CMD_REQUEST_POSITION_LOG       0x0005   //message ReportDataLog

#define MAXPB_CMD_FILE_CHANGE                0x0006   //message FileCommand
#define MAXPB_CMD_FILE_REQUEST_DATA          0x0007   //message FileTransfer 
#define MAXPB_CMD_FILE_DATA                  0x0008   //message FileTransfer
#define MAXPB_CMD_FILE_ERASE                 0x0009   //message FileErase 
#define MAXPB_CMD_FILE_CANCEL                0x000A   //message FileCommand
#define MAXPB_CMD_FILE_UPLOAD_INIT           0x000B   //message FileCommand
#define MAXPB_CMD_FILE_UPLOAD_REQUEST_DATA   0x000C   //message FileTransfer
#define MAXPB_CMD_FILE_UPLOAD_DATA           0x000D   //message FileTransfer
#define MAXPB_CMD_FILE_CHANGE_BY_DIFF        0x000E   //message FileCommand

#define MAXPB_CMD_REQUEST_STATUS             0x0010   //message BasicCommand
#define MAXPB_CMD_STATUS                     0x0011   //message ReportStatus
#define MAXPB_CMD_MULTIPLE_REPORT_LORA       0x0012   //message MultipleReportLora
#define MAXPB_CMD_REQUEST_SETUP              0x0013   //message BasicCommand
#define MAXPB_CMD_SETUP_DATA                 0x0014   //message ReportMaxConfig
#define MAXPB_CMD_REPORT_BLACKBOX            0x0015   //message ReportBlackBox
#define MAXPB_CMD_REQUEST_POSITION_IN_RAM    0x0016   //message BasicCommand
#define MAXPB_CMD_WRITE_RS232                0x0017   //message WriteRs232
#define MAXPB_CMD_OPEN_DATA_ADD              0x0018   //message OpenDataAdd
#define MAXPB_CMD_ROUTER                     0x0019   //message RoutePack
#define MAXPB_CMD_USER                       0x001A   //message UserCommand
#define MAXPB_CMD_ACCELEROMETER_EVENT_DETAIL 0x001B   //message ReportAccelerometerEventDetail
#define MAXPB_CMD_SCAN_OTHER_OPERATOR_CELLS  0x001C   //message BasicCommand
#define MAXPB_CMD_SET_INPUT_COUNTER          0x001D   //message SetInputCounter
#define MAXPB_CMD_REQUEST_LORA_SETUP         0x001E   //message BasicCommand
#define MAXPB_CMD_LORA_SETUP_DATA            0x001F   //message ReportLoraConfigPeripherals

#define MAXPB_CMD_SETUP_DEFAULT              0x0020   //message BasicCommand
#define MAXPB_CMD_PASSWORD                   0x0021   //message PasswordEnter
#define MAXPB_CMD_PASSWORD_STORE             0x0022   //message PasswordStore
#define MAXPB_CMD_SET_VARIABLES              0x0023   //message Variables
#define MAXPB_CMD_REQUEST_VARIABLES          0x0024   //message BasicCommand
#define MAXPB_CMD_VARIABLES_DATA             0x0025   //message Variables
#define MAXPB_CMD_FORMAT_POSITION_LOG        0x0026   //message BasicCommand
#define MAXPB_CMD_CLEAR_POSITION_LOG         0x0027   //message BasicCommand
#define MAXPB_CMD_EXECUTE_EMBEDDED_ACTION    0x0028   //message ExecuteEmbeddedAction
#define MAXPB_CMD_SET_VARIABLES_ON_FLASH     0x0029   //message Variables
#define MAXPB_CMD_REQUEST_LORA_WAN_NWK_LIST  0x002A   //message BasicCommand
#define MAXPB_CMD_LORA_WAN_NWK_LIST_DATA     0x002B   //message ReportLoraWANNetworkConfigList
#define MAXPB_CMD_REQUEST_TX_PACKET          0x002C   //message RequestTransmissionPacket
#define MAXPB_CMD_CLEAR_ECU_INFO             0x002D   //message BasicCommand
#define MAXPB_CMD_REQUEST_CUSTOM_REPORT_DATA 0x002E   //message BasicCommand
#define MAXPB_CMD_REPORT_SIGFOX              0x002F   //message SigfoxData

#define MAXPB_CMD_SET_POWER                  0x0030   //message SetPower 
#define MAXPB_CMD_SET_OUTPUT                 0x0031   //message SetOutput
#define MAXPB_CMD_SET_OPERATIONAL_STATE      0x0032   //message SetOperationalState
#define MAXPB_CMD_IGN_AUTO_CALIB             0x0033   //message BasicCommand
#define MAXPB_CMD_ACC_RESTART_CALIB          0x0034   //message BasicCommand
#define MAXPB_CMD_ACC_DEACTIVATE_CALIB       0x0035   //message BasicCommand
#define MAXPB_CMD_DISCONNECT                 0x0036   //message Disconnect
#define MAXPB_CMD_LORA_GATEWAY_CONTROL       0x0037   //message LoraGatewayCmd
#define MAXPB_CMD_LORA_COMMAND               0x0038   //message LoraCommand
#define MAXPB_CMD_SET_BLE_VARS               0x0039   //message SetBleVars
#define MAXPB_CMD_START_BLUETOOTH            0x003A   //message BasicCommand
#define MAXPB_CMD_FILE_EDIT                  0x003B   //message FileEdit
#define MAXPB_CMD_FILE_EDIT_RESULT           0x003C   //message FileEditResult
#define MAXPB_CMD_LOG_INFO_REQUEST           0x003D   //message BasicCommand
#define MAXPB_CMD_LOG_INFO_DATA              0x003E   //message ReportLogInfo
#define MAXPB_CMD_ACQUIRE_VEHICLE_SIGNATURE  0x003F   //message BasicCommand

#define MAXPB_CMD_POS_CONNECT                0x0106   //message BasicCommand
#define MAXPB_CMD_RS232_CONNECT              0x0107   //message BasicCommand
#define MAXPB_CMD_CHANGE_SETUP               0x0108   //message ChangeMaxConfig
#define MAXPB_CMD_CHANGE_MAXIO_SETUP         0x010B   //message ChangeMaxIOConfig

// MTs that can be used on ack new command
#define MAXPB_CMD_KEEP_CHANNEL_OPEN          0x0201
#define MAXPB_CMD_YOU_CAN_CLOSE_CHANNEL      0x0202

typedef union
{
   uint16 value;
   struct
   {
      uint16 cryptoType     :3;  // 2 bytes (original size) + data
      uint16 rfu1           :1;
      uint16 compressType   :2;
      uint16 rfu2           :9;
      uint16 ackRequired    :1;   //used for Commands and/or Report
   }info;
} PackageFormat_t;

typedef struct 
{
   uint32            header;
   uint16            size;
   uint16            crc;
   uint16            message_type;
   PackageFormat_t   format;
   uint8             data[];
} MaxPB_t;

typedef struct
{
   uint8_t             *buffer;
   uint8_t             state;
   uint16_t            size;
   uint16_t            max_size;
   uint16_t            waiting_size;
} MaxPB_Receiver_t;

#endif // _PROTOCOL_FRAME_
