#include "networkClass.h"
#include "networkField.h"
#include "networkRPC.h"

#include <cstddef>
#include <string>

#include "indent.h"

/**
 * Encodes all fields of this class into the datagram, including nested class
 * fields.
 */
void
NetworkClass::write(void *object, Datagram &dg) const {
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    NetworkField *field = _inherited_fields[i];
    field->write(object, dg);
  }
}

/**
 * Reads all fields from the datagram and stores them on the provided object.
 */
void
NetworkClass::read(void *object, DatagramIterator &scan) const {
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    NetworkField *field = _inherited_fields[i];
    field->read(object, scan);
  }
}

/**
 *
 */
void
NetworkClass::inherit_fields() {
  if (_built_inherited_fields) {
    return;
  }

  if (_parent != nullptr) {
    // Inherit fields from parent.
    // Make sure they've inherited their own fields too.
    _parent->inherit_fields();
    _inherited_fields.insert(_inherited_fields.end(),
                             _parent->_inherited_fields.begin(),
                             _parent->_inherited_fields.end());
    _inherited_rpcs.insert(_inherited_rpcs.end(),
                           _parent->_inherited_rpcs.begin(),
                           _parent->_inherited_rpcs.end());
  }

  // Add our own fields.
  _inherited_fields.insert(_inherited_fields.end(), _fields.begin(),
                           _fields.end());
  _inherited_rpcs.insert(_inherited_rpcs.end(), _rpcs.begin(), _rpcs.end());

  // Sort fields by name.
  std::sort(_inherited_fields.begin(), _inherited_fields.end(),
            [](NetworkField *a, NetworkField *b) { return a->name < b->name; });

  std::sort(_inherited_rpcs.begin(), _inherited_rpcs.end(),
            [](NetworkRPC *a, NetworkRPC *b) { return a->name < b->name; });

  _built_inherited_fields = true;
}

/**
 *
 */
void
NetworkClass::output(std::ostream &out, int indent_level) const {
  indent(out, indent_level) << "net class " << _name << "\n";
  indent(out, indent_level + 2) << "stride: " << _stride << " bytes\n";
  if (_parent != nullptr) {
    indent(out, indent_level + 2) << "parent: " << _parent->_name << "\n";
  } else {
    indent(out, indent_level + 2) << "no parent\n";
  }
  indent(out, indent_level + 2) << _inherited_fields.size() << " fields:\n";
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    _inherited_fields[i]->output(out, indent_level + 4);
  }
  indent(out, indent_level + 2) << _inherited_rpcs.size() << " rpcs\n";
  for (size_t i = 0; i < _inherited_rpcs.size(); ++i) {
    _inherited_rpcs[i]->output(out, indent_level + 4);
  }
}

/**
 *
 */
void NetworkClass::
construct_fields(void *object) const {
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    NetworkField *field = _inherited_fields[i];
    if (field->is_indirect()) {
      continue;
    }
    if (field->source_type == NetworkField::DT_string || field->source_type == NetworkField::DT_datagram) {
      unsigned char *data_ptr = (unsigned char *)object + field->offset;
      for (size_t j = 0; j < field->count; ++j) {
	if (field->source_type == NetworkField::DT_string) {
	  new(data_ptr) std::string();
	} else {
	  new(data_ptr) Datagram();
	}
	data_ptr += field->stride;
      }
    } else if (field->source_type == NetworkField::DT_class) {
      field->net_class->construct_fields((unsigned char *)object + field->offset);
    }
  }
}

/**
 *
 */
void NetworkClass::
destruct_fields(void *object) const {
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    NetworkField *field = _inherited_fields[i];
    if (field->is_indirect()) {
      continue;
    }
    if (field->source_type == NetworkField::DT_string || field->source_type == NetworkField::DT_datagram) {
      using string_type = std::string;
      unsigned char *data_ptr = (unsigned char *)object + field->offset;
      for (size_t j = 0; j < field->count; ++j) {
	if (field->source_type == NetworkField::DT_string) {
	  ((string_type *)data_ptr)->~string_type();
	} else {
	  ((Datagram *)data_ptr)->~Datagram();
	}
	data_ptr += field->stride;
      }
    } else if (field->source_type == NetworkField::DT_class) {
      field->net_class->destruct_fields((unsigned char *)object + field->offset);
    }
  }
}
