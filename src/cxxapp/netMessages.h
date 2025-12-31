#ifndef NETMESSAGES_H
#define NETMESSAGES_H

/**
 * Enumeration of low-level message types that can be sent/received by clients
 * and the server.
 */
class NetMessages {
public:
  enum MessageType {
    CL_hello,
    SV_hello_resp,

    CL_disconnect,

    SV_world_update,
    CL_world_update_ack,

    SV_set_object_owner,

    B_object_message,

    SV_generate_object,

    SV_disable_object,
    SV_delete_object,

    CL_ping,
    CL_inform_ping,
    SV_ping_resp,

    CL_add_interest,
    CL_remove_interest,
    CL_set_interest,
    SV_interest_complete,
  };
};

#endif // NETMESSAGES_H
