#include "viewModel.h"
#include "networkClass.h"

NetworkClass *ViewModel::_network_class = nullptr;

/**
 *
 */
ViewModel::
ViewModel() :
  _player_id(-1)
{
}

/**
 *
 */
void ViewModel::
init_network_class() {
  BEGIN_NETWORK_CLASS(ViewModel, Entity);
  MAKE_NET_FIELD(ViewModel, _player_id, NetworkField::DT_int32);
  END_NETWORK_CLASS();
}
